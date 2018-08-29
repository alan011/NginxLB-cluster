简要说明
===========

这是一套基于openresty封装的Nginx负载均衡集群系统。用反向代理的方式，实现内部服务的负载均衡。

支持七层反代，四层反代，七层黑白名单访问控制，流量切换等功能，支持集群自动初始化，自动扩容等功能。

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

接口说明
==========

本着前后端分离的开发原则，本系统将所有功能都先封装成了接口。


七层代理管理接口
----------

URI: /proxy/api/v1/httpproxy


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
