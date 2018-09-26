from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from jsonfield import JSONField

YES_or_NO=((0,'否'),(1,'是'))
# PUSH_STATS = ((0,"等待下发"), (1,"下发成功"),(2,"下发失败"),(3,"多次尝试后，配置仍无法应用到各节点，请联系管理员！"))
PUSH_STATS = ((0,"新应用，未曾推送过"),(1,"已成功推送过的应用"))
APPLY_STATS = ((0,"等待下发"),(1,"已生效"),(2,"下发失败"),(3,"下发成功，等待reload"))
CLUSTER_ROLES = (('MASTER','主节点'),('MINION','从节点'))

class HttpProxy(models.Model):
    TYPE = 'http'

    id                 = models.AutoField('ID',primary_key=True)
    proxy_domain_name  = models.CharField('代理域名', max_length=128, default='', unique=True)
    app_name           = models.CharField('代理应用',max_length=128, default='', unique=True)
    app_port           = models.IntegerField('应用端口', default=0)
    app_servers        = models.TextField('应用服务器', default='')
    app_servers_backup = models.TextField('热备服务器', default='')
    other_domain_names = models.TextField('其他代理域名', default='')
    proxy_listen_ports = models.TextField('监听端口', default='')
    description        = models.TextField('描述', default='')
    add_time           = models.DateTimeField('添加时间', default=timezone.now)
    add_user           = models.ForeignKey(User, on_delete=models.SET_NULL, related_name="my_httpproxies", null=True, blank=True)
    is_deleted         = models.IntegerField('是否删除',choices=YES_or_NO, default=0)
    is_disabled        = models.IntegerField('是否停用',choices=YES_or_NO, default=0)
    push_stat          = models.IntegerField('推送状态',choices=PUSH_STATS, default=0) ### 标识是否是新添加的应用代理。
    apply_stat         = models.IntegerField('下发状态',choices=APPLY_STATS, default=0) ### 标识配置是否成功推送到各个nginx节点，并在nginx中是否生效。


class TcpProxy(models.Model):
    TYPE = 'tcp'

    id                 = models.AutoField('ID',primary_key=True)
    proxy_domain_name  = models.CharField('代理域名', max_length=128, default='', unique=True)
    app_name           = models.CharField('应用名称',max_length=128, default='', unique=True)
    app_port           = models.IntegerField('应用端口', default=0)
    proxy_port         = models.IntegerField('代理端口', default=0, unique=True)
    app_servers        = models.TextField('后端服务器', default='')
    app_servers_backup = models.TextField('热备服务器', default='')
    description        = models.TextField('描述', default='')
    add_time           = models.DateTimeField('添加时间', default=timezone.now)
    add_user           = models.ForeignKey(User, on_delete=models.SET_NULL, related_name="my_tcpproxies", null=True, blank=True)
    is_deleted         = models.IntegerField('是否删除',choices=YES_or_NO, default=0)
    is_disabled        = models.IntegerField('是否停用',choices=YES_or_NO, default=0)
    push_stat          = models.IntegerField('推送状态',choices=PUSH_STATS, default=0) ### 标识是否是新添加的应用代理。
    apply_stat         = models.IntegerField('下发状态',choices=APPLY_STATS, default=0) ### 配置是否成功推送到各个nginx节点。

class AccessControlIPList(models.Model):
    id                 = models.AutoField('ID',primary_key=True)
    ip                 = models.CharField('IP地址',max_length=32, default='', unique=True)
    description        = models.TextField('描述', default='')
    add_time           = models.DateTimeField('添加时间', default=timezone.now)
    add_user           = models.ForeignKey(User, on_delete=models.SET_NULL, related_name="my_accessips", null=True, blank=True)
    is_deleted         = models.IntegerField('是否删除',choices=YES_or_NO, default=0)

class WhiteListStrategy(models.Model):
    TYPE = 'WhiteListStrategy'
    # PROXY_TYPE_CHOICES = (('http','七层代理'),('tcp','四层代理'))

    id                 = models.AutoField('ID',primary_key=True)
    strategy_name      = models.CharField('策略名称',max_length=128, default='', unique=True)
    # proxy_domain_name  = models.CharField('所属应用代理',max_length=128, default='', unique=True)
    proxy_belong       = models.OneToOneField(HttpProxy, on_delete=models.SET_NULL, related_name="whitelist_refers", null=True, blank=True)
    # proxy_type         = models.CharField('所属代理类型',max_length=8, choices=PROXY_TYPE_CHOICES, default='http')
    iplist             = models.ManyToManyField(AccessControlIPList, related_name='whitelist_refers')
    description        = models.TextField('描述', default='')
    add_time           = models.DateTimeField('添加时间', default=timezone.now)
    add_user           = models.ForeignKey(User, on_delete=models.SET_NULL, related_name="whitelist_refers", null=True, blank=True)
    is_deleted         = models.IntegerField('是否删除',choices=YES_or_NO, default=0)
    is_disabled        = models.IntegerField('是否停用',choices=YES_or_NO, default=0)
    push_stat          = models.IntegerField('推送状态',choices=PUSH_STATS, default=0) ### 标识是否是新添加的应用代理。
    apply_stat         = models.IntegerField('下发状态',choices=APPLY_STATS, default=0) ### 配置是否成功推送到各个nginx节点。

class BlackListStrategy(models.Model):
    TYPE = 'BlackListStrategy'
    # PROXY_TYPE_CHOICES = (('http','七层代理'),('tcp','四层代理'))

    id                 = models.AutoField('ID',primary_key=True)
    strategy_name      = models.CharField('策略名称',max_length=128, default='', unique=True)
    # proxy_domain_name  = models.CharField('所属应用代理',max_length=128, default='', unique=True)
    proxy_belong       = models.OneToOneField(HttpProxy, on_delete=models.SET_NULL, related_name="blacklist_refers", null=True, blank=True)
    # proxy_type         = models.CharField('所属代理类型',max_length=8, choices=PROXY_TYPE_CHOICES, default='http')
    iplist             = models.ManyToManyField(AccessControlIPList, related_name='blacklist_refers')
    description        = models.TextField('描述', default='')
    add_time           = models.DateTimeField('添加时间', default=timezone.now)
    add_user           = models.ForeignKey(User, on_delete=models.SET_NULL, related_name="blacklist_refers", null=True, blank=True)
    is_deleted         = models.IntegerField('是否删除',choices=YES_or_NO, default=0)
    is_disabled        = models.IntegerField('是否停用',choices=YES_or_NO, default=0)
    push_stat          = models.IntegerField('推送状态',choices=PUSH_STATS, default=0) ### 标识是否是新添加的应用代理。
    apply_stat         = models.IntegerField('下发状态',choices=APPLY_STATS, default=0) ### 配置是否成功推送到各个nginx节点。


class ClusterMember(models.Model):
    #INIT_STAT = ((0,'未初始化'),(1,'已初始化'),(2,'等待生效的master'), (3,'等待移除master角色'))
    INIT_STAT = ((0,'未初始化'),(1,'已初始化'))
    ALIVE_STAT = ((0, '等待被master接受'), (1, '状态正常'), (2, 'salt-minion状态异常'),(3,'nginx状态异常'),(4,'Master is down!'))
    id                 = models.AutoField('ID',primary_key=True)
    ip                 = models.CharField('IP地址',max_length=32, default='', unique=True)
    hostname           = models.CharField('主机名',max_length=128, default='')
    role               = models.CharField('集群角色', max_length=16, choices=CLUSTER_ROLES, default='MINION')
    is_init            = models.IntegerField('是否初始化',choices=INIT_STAT, default=0) #安装salt-minion, 优化系统参数。
    is_alive           = models.IntegerField('是否存活',choices=ALIVE_STAT, default=0) #主要检查是否还受salt-master控制。
    need_reload        = models.IntegerField('是否需要reload',choices=YES_or_NO, default=0)
    is_deleted         = models.IntegerField('是否删除', choices=YES_or_NO, default=0)

class NLBConfig(models.Model):
    NAMES = (('initConfig','初始化配置'),)
    id                 = models.AutoField('ID',primary_key=True)
    name               = models.CharField('配置项目',max_length=16, choices=NAMES, default='', unique=True)
    content            = JSONField(default={})   ### 存储字符串键值对儿。

class PushLog(models.Model):
    TYPE_CHOICES = (('http', '七层代理'),('tcp', '四层代理'),('whitelist','白名单'))
    id                 = models.AutoField('ID',primary_key=True)
    type               = models.CharField('应用类型',max_length=16, choices=TYPE_CHOICES, default='')
    target_id          = models.IntegerField('应用ID', default=-1)
    log_path           = JSONField('日志路径', default={})
    message            = models.TextField('错误消息', default='')
    push_time          = models.DateTimeField('推送时间', default=timezone.now)
