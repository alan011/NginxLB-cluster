from django.views.generic import View
from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from nlb_proxy.models import ClusterMember, NLBConfig
from nlb_proxy.tools import validateIP
from nlb_proxy import config

import re,json

@method_decorator(csrf_exempt, name='dispatch')
@method_decorator(login_required, name='dispatch')
class NLBCluster(View):
    def __init__(self, *args, **kwargs):
        self.response_data = {'result':'SUCCESS','message':''}
        self.status = 200
        super().__init__(*args, **kwargs)

    def checkIP(self, ip):
        queryset = ClusterMember.objects.filter(ip = ip)
        if not queryset.exists():
            return None
        else:
            return queryset.get(ip = ip)

    def saveObject(self, obj):
        obj.save()
        try:
            obj.save()
        except:
            self.response_data.update({'result':'FAILED', 'message':"错误：数据库错误，请联系管理员！"})
            self.status = 500
            return False
        else:
            return True

    def getInit(self):
        init_setting = {'sysuser':'',
                        'syspasswd':'',
                        'sethostname':'',
                        'hostnameprefix':'NLB-CLUSTER',
                       }
        queryset = NLBConfig.objects.filter(name='initConfig')
        if queryset.exists():
            obj = queryset.get(name='initConfig')
            init_setting = obj.content

        self.response_data['initSetting'] = init_setting

    def setInit(self):
        new_setting = {}
        error_count = 0
        if self.post_data.get('sysuser'):
            new_setting['sysuser'] = self.post_data['sysuser']
        else:
            error_count += 1
        if self.post_data.get('syspasswd'):
            new_setting['syspasswd'] = self.post_data['syspasswd']
        else:
            error_count += 1
        if self.post_data.get('sethostname') == 'Y':
            new_setting['sethostname'] = self.post_data['sethostname']
            if self.post_data.get('hostnameprefix'):
                new_setting['hostnameprefix'] = self.post_data['hostnameprefix']
            else:
                new_setting['hostnameprefix'] = 'NLB-CLUSTER'
        else:
            new_setting['sethostname'] = 'N'

        if error_count:
            self.response_data.update({'result':'FAILED','message':'错误：请提供操作系统用户名/密码'})
            self.status = 400
        else:
            queryset  = NLBConfig.objects.filter(name='initConfig')
            if queryset.exists():
                obj = queryset.get(name='initConfig')
            else:
                obj = NLBConfig(name='initConfig')
            obj.content = new_setting
            self.saveObject(obj)

    def expandCluster(self):
        ips = self.post_data.get('ip_list')
        if ips:
            ip_list = ips.split('\n')
            # print(ip_list)
            is_ip = True
            for ip in ip_list:
                if not validateIP(ip):
                    is_ip = False
                    self.response_data.update({'result':'FAILED','message':"错误：发现无效IP '%s'!" % ip})
                    self.status=400
                elif self.checkIP(ip):
                    is_ip = False
                    self.response_data.update({'result':'FAILED','message':"错误：IP '%s'已在集群中存在!" % ip})
                    self.status=400
            if is_ip:
                for ip in ip_list:
                    obj = ClusterMember(ip=ip)
                    if not self.saveObject(obj):
                        break

    def kickoffNode(self):
        ip = self.post_data.get('ip')
        if ip:
            obj = self.checkIP(ip)
            if obj:
                obj.delete();

    def setMaster(self):
        ip = self.post_data.get('ip')
        if ip:
            obj = self.checkIP(ip)
            if obj:
                obj.role = 'MASTER'
                obj.is_init = 2
                self.saveObject(obj)

    def setMinion(self):
        ip = self.post_data.get('ip')
        if ip:
            obj = self.checkIP(ip)
            if obj:
                obj.role = 'MINION'
                obj.is_init = 3
                self.saveObject(obj)

    def get(self, request, *args, **kwargs):
        queryset = ClusterMember.objects.all()
        data = []
        for node in queryset:
            attr = {'hostname':node.hostname,
                    'ip':node.ip,
                    'role':node.role,
                    'status':('未知','red'),
                 }
            if not node.hostname:
                attr['hostname'] = '获取主机信息中...'
            elif node.is_init == 0:
                attr['status'] = ('未初始化','gray')
            elif node.is_alive == 0:
                attr['status'] = ('等待被master接受','orange')
            elif node.is_alive == 1:
                attr['status'] = ('运行正常','green')
                if node.need_reload == 1:
                    attr['status'] = ('配置更新自动reload失败,请联系管理员排查', 'red')
            elif node.is_alive == 2:
                attr['status'] = ('salt-minion异常','red')
            elif node.is_alive == 3:
                attr['status'] = ('nginx异常','red')
            elif node.is_alive == 4:
                attr['status'] = ('不能连接到master','red')

            data.append(attr)
        self.response_data['data'] = data

        return HttpResponse(json.dumps(self.response_data),content_type='application/json',status=self.status)

    def post(self, request, *args, **kwargs):
        legal_action = ['getInit', 'setInit', 'setMaster',  'setMinion','expandCluster', 'kickoffNode']
        self.post_data = {k:v.strip() for k,v in request.POST.items()}
        # print(self.post_data)

        action = self.post_data.get('action')
        if action in legal_action:
            getattr(self, action)()
        else:
            self.response_data.update({'result':'FAILED','message':"ERROR: action '%s' not support." % action})
            self.status = 400

        # print("response_data: %s; status: %s" % (self.response_data,self.status))
        return HttpResponse(json.dumps(self.response_data),content_type='application/json',status=self.status)
