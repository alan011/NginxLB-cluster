daemon程序的构思逻辑
=======


本文旨在大体说明daemon程序的主要构思逻辑。


文档摘要
------
编写时间：2018-06-13

作者：雷海龙

作者email：leihailong@hfbank.com.cn/alan001lhl@sina.com


功能概要
------

daemon程序，主要包含以下四个任务（每个任务即是daemon程序的一个子进程）：

* server_init:  集群初始化
* manage_keys:  集群成员key的管理
* apply_config: 应用配置推送
* health_check: 成员健康检查

daemon作为一个timer型的程序，是独立于web服务进程的。每隔一定时间便会并行启动以上四个子进程，开始工作。

间隔时间由这个配置项来指定：`nlb_proxy.config.TIMER_RUNTIME_INTERVAL`

对于以上四个任务，daemon程序作了进程唯一处理。即，当进入下一次循环，而上一次循环中启动的子进程还未完成时，daemon程序不会启动新的子进程来做相同的任务，以保证处理同一任务的进程唯一。

daemon程序的所有输出信息，都由日志记录，日志路径定义在配置项：`nlb_proxy.config.TIMER_LOG_PATH`

下面分别对以上四个任务的实现做简要说明。


server_init
----------

<待续>


manage_keys
----------

<待续>



apply_config
----------

<待续>



health_check
----------

集群成员的健康状态分以下五种情况
(记录在model字段：`nlb_proxy.models.ClusterMember.is_alive`)：

* (0, "没有被master接受")

    表示这是做完初始化的机器，但是它作为minion的key，还没有被salt-master接受。

    出现这种状态的话，一般等待daemon程序调动master自动接受即可；若是有问题，需要去查daemon程序的日志，排查问题。

* (1, "状态正常")

    表示这台机器的所有状态均正常，是一台健康的机器。

* (2, "salt-minion状态异常")

    表示这台机器作为一台minion已无法跟master通信，master无法控制它了。

    出现这种情况，一般是因为salt-minion挂了，或者key发生了变动。需要系统管理员手动处理。

* (3, "nginx状态异常")

    表示salt-minion状态正常，但nginx服务挂了。需要管理员排查nginx问题。

* (4, "salt-master异常")

    表示salt-master状态有问题，比如salt-master进程挂了，或者master节点未设置，或者master被移除了集群。

    检测到salt-master出问题后，health_check进程会将所有成员标注为此状态，直到管理员手工恢复集群。
    》》》如何自动恢复？？？，好像没有处理逻辑《《《


health_check按照如下逻辑顺序执行：

* 首先，检查salt-minion状态

    在salt-master上对所有minion做salt的test.ping操作，返回True就认为salt-minion状态正常，否则认为异常。

    异常的机器健康状态将被设置为2，表示不受master控制的机器。处于这种状态的机器，配置文件是不可信的，有可能跟数据库不同步。

    当机器的状态由2变为1时，即恢复健康时，health_check进程会从集群中任意找一台健康的机器（以上一次的检查结果为准）为基准，将机器的配置数据clone给刚刚恢复健康的机器，并触发自动推送，以保证恢复的机器配置数据可信。

    若没有健康的机器作为基准，则无法clone,这表示整个集群都down了。

    注意，出现这种极端情况时，nginx服务有可能是仍然处于在线状态的。只是本系统的集群管理不再可用，本系统不会再对nginx的应用配置做任何修改，以保证服务稳定。

    》》》具体如何处理，能不能程序自动处理？？？《《《
    》》》可以在“集群管理”界面，开发一个“同步数据库”的按钮，让所有机器重新以数据库为基准同步nginx配置文件《《《

* 然后，检查各机器nginx的状态

    利用salt，对每台状态为1或3的机器，远程执行`nlb_proxy/scripts/service_check.sh`脚本，检测return_code，若为0，则认为机器正常；非0，即nginx状态异常。

    注意，其他状态的机器是不需要做这项检查的。

* 最后，reload各台机器nginx服务。

    用户在界面修改了应用配置参数，apply_config进程会下发更新的配置文件（注意，下发文件不自动reload nginx），并在数据库中标记各台nginx节点为需要reload的状态。

    此状态由model字段`nlb_proxy.models.ClusterMember.need_reload`记录。

    health_check进程根据这个字段来对需要reload的机器做reload操作。

    》》》reload操作对各种非健康机器是如何处理的？《《《
