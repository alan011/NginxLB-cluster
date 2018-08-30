简要说明
===========

这是一套基于openresty封装的Nginx负载均衡集群系统。用反向代理的方式，实现内部服务的负载均衡。

支持七层反代，四层反代，七层黑白名单访问控制，流量切换等功能，支持nginx集群自动初始化，自动扩容等功能。

底层用Django开发的一套API，web用vue.js开发。集群初始化走ssh通道。代理配置同步使用geniusalt来分发文件。

本系统定位在于给运维人员使用，暂无复杂权限管理机制，只有简单的用户增删的功能。

关于geniusalt请，参考项目：https://github.com/alan011/geniusalt-apiserver

系统构成由三部分组成：

* api-server

    Django开发的一套API，封装了所有功能。    

* web界面

    Vue.js结合element-ui开发的一套简洁的界面。使用AJAX跟api-server对接。

* 后台Daemon程序

    第一个独立于api-server的python进程。需要单独启动。相当于一个timer程序，实现了集群自动初始化、自动下发配置的变更、集群健康检查等功能。


安装使用
===========

运行环境：
* OS: centos6.x
* 语言: python-3.5 以上
* 框架: django-1.11.x
* pip3依赖包: PyYaml, jsonfield, paramiko, requests
* 底层依赖-1：openresty，请确保集群中所有机器可以通过yum安装openresty软件包。
* 底层依赖-2：saltstack，请确保正确安装、启动了salt-master服务。这意味着，本软件包安装的机器，即是集群的master。

开发测试基于Chrome，请使用Chrome浏览器。

安装方法：
* 下载本项目所有源码，解压至一个目录。
* 设置django配置文件: `hfnlb_project/hfnlb_project/settings.py`, 修改`ALLOWED_HOSTS`,`DATABASES`两个配置项，并根据DB的配置，创建相应的库。
* 启动web服务：到`hfnlb_project/`目录下，启动`start.sh`
* 启动Daemon程序：到`hfnlb_project/nlb_proxy/bin`目录下，执行`nohup ./nlb_timer &`

注意：
* `start.sh`中默认启动`0.0.0.0:10080`，可根据自己需求修改。
* `start.sh`这种启动方式，仅供测试、体验用。若要用到高并发环境中，请使用`nginx + uWSGI` 来启动web服务。



集群管理
===========

本系统提供了自动化的集群管理机制。意味着，除了master需手动安装外，其他成员均可自动完成初始化，应用配置自动同步。

但，以上的自动化集群管理，依赖几个前提条件：

* 可用统一系统用户通过ssh登录到所有成员机器

    集群中所有机器，请使用同一的系统 user/password，并且user能有无密sudo权限。
    这样master可以通过ssh通道登录到目标机器上，执行成员机器的初始化工作。
    这个系统用户，可以在界面中的“集群管理”，“初始化设置”中设定。

* 确保可以通过yum安装所需软件包

    各成员机器，所需系统软件包：salt-minion, openresty.

* 确保nlb_timer程序已启动

满足以上条件后，要为此Nginx集群添加成员，在“集群管理”栏，添加IP列表即可。集群可自动完成初始化，自动同步已有应用配置。

注意：一般情况下，NLB集群上游会挂一个四层负载均衡器（比如F5, LVS等），新成员的IP需要管理员手动加到上游负载均衡池。目前还没有实现这块的自动添加功能。


接口说明
==========

本着前后端分离的开发原则，本系统将所有功能都先封装成了接口。
注意：所有接口都要求用户先登录才能正常使用。


七层代理管理接口
----------

URI: `/proxy/api/v1/httpproxy`

返回数据：所有接口均返回一个json字典，如下。
```
{   "result":"SUCCESS",     #表示接口执行结果，成功是“SUCCESS", 失败是“FAILED”
    "message":"<文本信息>",  #一段返回的文本信息。
    ...                     #对GET方法，请求的结果，还会增加一个'data'字段，具体见下文。
}
```

接口调用逻辑：

* 获取全部信息  

    方法：GET

    参数：无

    返回数据：在上文所说的json字典中会增加一个‘data’字段，其值是一个list，list是一个表征每条应用代理配置的属性与状态的字典。

* 检索、过滤信息：

    方法：GET

    参数：search_value

    返回数据：在上文所说的json字典中会增加一个‘data’字段，其值是一个list，list是一个表征每条应用代理配置的属性与状态的字典。

    说明：用search_value参数来支持复杂检索模式。支持以下检索、过滤规则：

    * 全字段模糊搜索

        支持以下字段的单值模糊匹配：域名(DOMAIN，包含代理域名和其他域名)，应用(APP)，应用端口(APP_PORT)，监听端口(LISTEN_PORT)，服务器(SERVER，包含应用服务器和热份服务器)，用户(USER)，描述(DESC)。
        即用search_value的值去匹配数据库中的以上所有字段。

    * 指定字段进行模糊匹配：DOMAIN:<域名>&APP:<应用>...

        “:”用于模糊匹配。相对“全字段”而言，这里仅匹配指定的字段。

    * 指定字段进行精确匹配：DOMAIN=<域名>&APP=<应用>...

        “=”用于精确匹配。

    * 输入格式不满足第二、三条时，将默认触发第一条“全字段模糊搜索”。

* 增

    方法: POST

    数据格式: Form表单

    post数据字段:

    ```
{   "action":"add",                      #必填字段，表示要执行添加动作。
    "proxy_domain_name":"<反向代理域名>",   #必填字段，用于servername.
    "app_name":"<被代理的应用名称>",         #必填字段，用于命名upstream.
    "app_port":"<被代理的应用端口>",         #必填字段，用于upstream中，定义后端机器的服务端口转发。
    "app_servers":"<被代理应用的运行服务器>"  #必填字段，用于upstream中，定义后端机器成员。多个用'/'隔开。

    "app_servers_backup":"<被代理应用的运行服务器热备机器>"   #可选字段，多个用'/'隔开，成员需是‘app_servers’的子集。
    "other_domain_names":"<额外的servername>"             #可选字段，多个用'/'隔开
    "proxy_listen_ports":"<额外的nginx listen端口>"        #可选字段，不指定的话，nginx默认监听80。多个用'/'隔开。
    "description":"<文字描述>"                            #文字描述
}
    ```

* 删：

    方法: POST

    数据格式: Form表单

    post数据字段:

    ```
    {"action":"delete",            #必填字段，表示要执行删除动作。
    "id":"<应用代理数据库ID>"        #必填字段
    }
    ```

* 改：

    方法: POST

    数据格式: Form表单

    post数据字段:

    ```
    {"action":"edit",           #必填字段，表示要执行修改动作。
    "id":"<应用代理数据库ID>",    #必填字段
    ...                         #'add'方法中所陈述的字段，均支持修改。                             
    }
    ```

* 停用

    方法: POST

    数据格式: Form表单

    post数据字段:

    ```
    {"action":"disable",         #必填字段，表示要执行停用动作。
    "id":"<应用代理数据库ID>",     #必填字段                        
    }
    ```

* 启用

    方法: POST

    数据格式: Form表单

    post数据字段:

    ```
    {"action":"enable",         #必填字段，表示要执行添加动作。
    "id":"<应用代理数据库ID>",    #必填字段                        
    }
    ```

* 重新标记推送

    方法: POST

    数据格式: Form表单

    post数据字段:

    ```
    {"action":"saltRepush",         #必填字段，表示要将此条代理配置标记为未推送，让daemon程序重新触发推送逻辑。
    "id":"<应用代理数据库ID>",    #必填字段                        
    }
    ```

* 获取推送日志

    方法: POST

    数据格式: Form表单

    post数据字段:

    ```
    {"action":"getPushLog",         #必填字段，用于获取此条代理配置的saltstack推送日志。
    "id":"<应用代理数据库ID>",    #必填字段                        
    }
    ```



四层代理管理接口
----------

URI: /proxy/api/v1/tcpproxy


访问IP管理接口
----------

URI: /proxy/api/v1/iplist


白名单管理接口
----------

URI: /proxy/api/v1/whitelist


黑名单管理接口
----------

URI: /proxy/api/v1/blacklist


集群管理接口
----------

URI: /proxy/api/v1/cluster


用户管理接口
----------

URI: /proxy/api/v1/users


用户登录接口
----------

URI: /proxy/api/v1/login


用户信息查询接口
----------

URI: /proxy/api/v1/userinfo


Daemon程序说明
============

<未完待续>
