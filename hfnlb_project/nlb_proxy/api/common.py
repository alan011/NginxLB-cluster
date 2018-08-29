from django.views.generic import View
from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
from django.utils import timezone

from nlb_proxy.tools import validateIP, unique_list_elements
from nlb_proxy.models import AccessControlIPList, PushLog, HttpProxy
from nlb_proxy.daemon.apply_handler import ApplyHandler

import re,json,os


class APIMixin(object):
    """
    To define a set of attributes and method for API views that has saltstack-pillar-related data.
    """
    model = None
    fields_required = None
    fields_optional = None
    post_data = None
    legal_action = ['add', 'edit','delete', 'changePasswd']
    response_data = {'result':'SUCCESS', 'message':'OK'}
    status=200

    def dataVerify(self):
        """
        To verify post data from user.
        """
        ### Need to be rewrite by subclass, and return a 'post_data' dict
        pass

    def checkExistsWithFilterList(self, filter_list):
        for filter in filter_list:
            queryset = self.model.objects.filter(**filter)
            if queryset.exists():
                obj = queryset.get(**filter)
                if obj.is_deleted == 0:
                    return (1, obj, "Object already exist.")
                else:
                    return (2, obj, "Deleted")
        return (0, None, 'Not exist')

    def checkID(self):
        id = self.post_data.get('id')
        if not re.search('^\d+$', str(id)):
            self.response_data.update({'result':'FAILED', 'message':'ERROR: Illegal ID provided: %s !' % id})
            self.status = 400
            return None
        else:
            id = int(id)
            queryset = self.model.objects.filter(id=id, is_deleted=0)
            if not queryset.exists():
                self.response_data.update({"result':'FAILED', 'message':'ERROR: object with ID '%s' not exist!" % id})
                self.status = 404
                return None
            else:
                return queryset.get(id=id, is_deleted=0)

    def saveObject(self, obj):
        try:
            obj.save()
        except:
            self.response_data.update({'result':'FAILED', 'message':"ERROR: DB related error occurred while trying to save object!"})
            self.status = 500
            return False
        else:
            return True

    def checkExists(self):
        """
        To check whether object has aready existed or not with post data, when try to add a new object.
        """
        ### Need to be rewrite by subclass, and return a tuple: (check_code, obj, message)
        ### 'check_code': 0, 1, or 2. 0 means object not exists, 1 means object exists in db and not be marked deleted, 2 meams object exists but has been marked deleted.
        ### 'obj': None is 'check_code' is 0. Or an object queried from db.
        ### 'message': a string. Only works if check_code is 1. To return error message to user.
        pass

    def fillSystemAttrs(self, post_data):
        """
        Only used for add() method.
        """
        post_data['add_user']   = self.request.user
        post_data['add_time']   = timezone.now()
        post_data['is_deleted'] = 0

    def add(self):
        post_data = self.dataVerify()
        if isinstance(post_data, str):
            self.response_data.update({'result':'SUCCESS','message':post_data})
            self.status = 400
        else:
            check_code, obj, message = self.checkExists(post_data)
            # print(message)
            if check_code == 0:
                self.fillSystemAttrs(post_data)
                obj = self.model(**post_data)
                self.saveObject(obj)
                return obj, post_data
            elif check_code == 1:
                self.response_data.update({'result':'FAILED', 'message':message})
                self.status = 400
            else:
                self.fillSystemAttrs(post_data)
                # print(post_data)
                for attr in post_data:
                    setattr(obj, attr, post_data[attr])
                self.saveObject(obj)
                return obj, post_data
        return None, post_data

    def delete(self):
        obj = self.checkID()
        if obj is not None:
            obj.is_deleted = 1
            self.saveObject(obj)

    def edit(self):
        obj = self.checkID()
        post_data = self.dataVerify()
        if obj is not None:
            if isinstance(post_data, str):
                self.response_data.update({'result':'SUCCESS','message':post_data})
                self.status = 400
            else:
                changed = 0
                pillar_changed = 0
                for k in post_data:
                    if getattr(obj, k) != post_data[k]:
                        setattr(obj, k, post_data[k])
                        changed += 1
                if changed:
                    self.saveObject(obj)
                return obj, post_data
        return None, post_data

    def changePasswd(self):
        old_password = str(self.post_data.get('old_password'))
        if not self.request.user.check_password(old_password):
            self.response_data.update({'result':'FAILED',"message":"旧密码校验失败！"})
            self.status=403
        else:
            new_password = str(self.post_data.get('new_password')).strip()
            confirm_password = str(self.post_data.get('confirm_password')).strip()
            # print("new_password: %s, confirm_password: %s" % (new_password,confirm_password))
            if new_password != confirm_password:
                self.response_data.update({'result':'FAILED',"message":"新密码不匹配！"})
                self.status=400
            else:
                self.request.user.set_password(new_password)
                self.saveObject(self.request.user)

    def searchData(self):
        """
        To search data in DB when user click search button.
        """
        ### Need to be rewrite by subclass, and return a queryset.
        pass
        return []

    def getAll(self):
        return self.model.objects.filter(is_deleted=0).order_by('-id')

    def makeDataList(self, queryset):
        """
        To make data list from data queryset. This data list is used for table data on web page rendering.
        """
        ### Need to be rewrite by subclass, and return a data list
        pass

    def get(self, request, *args, **kwargs):
        if request.GET.get('search_value'):
            queryset = self.searchData()
        else:
            queryset = self.getAll()
        self.response_data['data'] = self.makeDataList(queryset)
        return HttpResponse(json.dumps(self.response_data), content_type='application/json',status=self.status)

    def post(self, request, *args, **kwargs):
        self.post_data = {k:v for k,v in self.request.POST.items()}
        if self.post_data['action'] not in self.legal_action:
            self.response_data.update({'result':'FAILED','message':"ERROR: Illegal operation: %s" % self.post_data['action']})
            self.status=400
        else:
            action = self.post_data.pop('action')
            getattr(self, action)()

        return HttpResponse(json.dumps(self.response_data), content_type='application/json', status=self.status)


class APISaltPushMixin(APIMixin):
    """
    To define a set of attributes and method for API views that has saltstack-pillar-related data.
    """
    legal_action = ['add', 'edit','delete','disable', 'enable', 'changePasswd', 'getPushLog', 'saltRepush']
    def disable(self):
        obj = self.checkID()
        if obj is not None:
            obj.is_disabled = 1
            obj.apply_stat = 0
            self.saveObject(obj)

    def enable(self):
        obj = self.checkID()
        if obj is not None:
            obj.is_disabled = 0
            obj.apply_stat = 0
            self.saveObject(obj)

    def getPushLog(self):
        obj = self.checkID()
        if obj is not None:
            queryset = PushLog.objects.filter(type=self.model.TYPE,target_id=obj.id).order_by('-push_time')
            logs = ''
            for log_obj in queryset:
                logs += '=======> push at %s:\n' % log_obj.push_time.strftime('%F %T')
                log_path = log_obj.log_path
                if log_path:
                    for n in log_path:
                        file_path = log_path[n]
                        if os.path.isfile(file_path):
                            logs += open(file_path).read() + '\n'
                        else:
                            logs += '(ERROR: log file not exists: %s)\n' % file_path
                else:
                    logs += log_obj.message + '\n'
                logs += '\n'
            if not logs:
                logs = '(No logs found!)'
            self.response_data.update({'result':'SUCCESS', 'logs':logs})

    def saltRepush(self):
        obj = self.checkID()
        if obj is not None:
            obj.apply_stat=0
            self.saveObject(obj)

    def fillSystemAttrs(self, post_data):
        super().fillSystemAttrs(post_data)
        post_data['is_disabled'] = 0
        post_data['push_stat']   = 0
        post_data['apply_stat']  = 0

    def delete(self):
        obj = self.checkID()
        if obj is not None:
            if obj.push_stat == 0:
                obj.is_deleted = 1
                self.saveObject(obj)
            else:
                if obj.is_disabled == 1:
                    if obj.apply_stat == 1:
                        obj.is_deleted = 1
                        self.saveObject(obj)
                    else:
                        self.response_data.update({'result':'FAILED', 'message':'ERROR: Please wait until this disabled app to be applied successfully.'})
                        self.status = 400
                else:
                    self.response_data.update({'result':'FAILED', 'message':'ERROR: Please to disable this app first.'})
                    self.status = 400

    def edit(self):
        obj = self.checkID()
        post_data = self.dataVerify()
        pillar_attrs = None
        if obj is not None:
            if isinstance(post_data, str):
                self.response_data.update({'result':'SUCCESS','message':post_data})
                self.status = 400
            else:
                apply_handler = ApplyHandler()
                pillar_attrs = apply_handler.getModulePillars(apply_handler.model_to_module[self.model])
                print(pillar_attrs)
                if pillar_attrs is not None:
                    changed = 0
                    pillar_changed = 0
                    for k in post_data:
                        if getattr(obj, k) != post_data[k]:
                            setattr(obj, k, post_data[k])
                            changed += 1
                            if k in pillar_attrs:
                                pillar_changed += 1
                    if pillar_changed:
                        obj.apply_stat = 0
                    if changed:
                        self.saveObject(obj)
                    return obj, post_data, pillar_attrs
                else:
                    self.response_data.update({'result':'FAILED', 'message':'ERROR: Cannot get module pillars in geniusalt.'})
                    self.status = 400

        return None, post_data, pillar_attrs

class APIStrategySaltPushMixin(APISaltPushMixin):
    legal_action = ['add', 'edit','delete','disable', 'enable', 'changePasswd', 'getPushLog', 'saltRepush', 'getProxiesAndIPs']
    fields_required = ['strategy_name','proxy_domain_name','iplist']
    fields_optional = ['description']
    access_ip_objs = None

    def dataVerify(self):
        form_data = {k:v.strip() for k,v in self.post_data.items() if k in self.fields_required + self.fields_optional}

        ### Check fields required.
        for field in self.fields_required:
            if field not in form_data:
                return "ERROR: Field '%s' is required!" % field

        ### Check 'strategy_name'
        if re.search('[^a-z0-9\-_]', form_data['strategy_name']):
            return "ERROR: Illegal value detected for field 'strategy_name': '%s'" % form_data['strategy_name']

        ### Check 'proxy_domain_name'
        if re.search('[^a-z0-9\-\.]', form_data['proxy_domain_name']):
            return "ERROR: Illegal value detected for field 'proxy_domain_name': '%s'" % form_data['proxy_domain_name']
        else:
            filter = {'is_deleted':0, 'proxy_domain_name':form_data['proxy_domain_name']}
            proxy_obj_queryset = HttpProxy.objects.filter(**filter)
            if proxy_obj_queryset.exists():
                proxy_obj = proxy_obj_queryset.get(**filter)
                form_data['proxy_belong'] = proxy_obj
                form_data.pop('proxy_domain_name')
            else:
                return "ERROR: http proxy object not found with 'proxy_domain_name': '%s'" % form_data['proxy_domain_name']

        ### Check 'iplist',
        access_ip_list = unique_list_elements(form_data['iplist'].split('/'))
        self.access_ip_objs = []
        for ip in access_ip_list:
            ip_obj_queryset = AccessControlIPList.objects.filter(ip=ip)
            if ip_obj_queryset.exists():
                self.access_ip_objs.append(ip_obj_queryset.get(ip=ip))
            else:
                return "ERROR: access IP object not found with ip '%s'" % ip
        form_data.pop('iplist')

        return form_data

    def checkExists(self, verified_data):
        filter_list = [{'proxy_belong':verified_data['proxy_belong']},
                       {'strategy_name':verified_data['strategy_name']},
                      ]
        return self.checkExistsWithFilterList(filter_list)

    def normalSearch(self, search_value):
        return self.model.objects.filter(is_deleted = 0).filter(Q(proxy_domain_name__icontains= search_value )|Q(strategy_name__icontains= search_value )|Q(description__icontains= search_value )|Q(add_user__username__icontains= search_value ))

    def searchData(self):
        return self.normalSearch(self.request.GET.get('search_value')).order_by('-id')

    def makeDataList(self, queryset):
        data = []
        for obj in queryset:
            attrs = {'id': obj.id,
                    'strategy_name': obj.strategy_name,
                    'proxy_domain_name': obj.proxy_belong.proxy_domain_name,
                    'iplist':[ ip.ip for ip in obj.iplist.filter(is_deleted=0)],
                    'description': obj.description,
                    'add_time': obj.add_time.strftime('%F %T'),
                    'add_user': obj.add_user.username,
                    'status': ['已生效', 'green'],
                    }

            if obj.proxy_belong.is_deleted != 0:
                attrs['proxy_domain_name'] += '（已删除）'

            if obj.apply_stat == 0:
                attrs['status'] = ["下发中", "orange"]
            elif obj.apply_stat == 2:
                attrs['status'] = ["下发失败","red"]
            elif obj.apply_stat == 3:
                attrs['status'] = ["下发成功，等待reload","blue"]
            elif obj.is_disabled:
                attrs['status'] = ['已停用', "gray"]
            data.append(attrs)
        return data

    def getProxiesAndIPs(self):
        self.response_data['ips'] = [ ip.ip for ip in AccessControlIPList.objects.filter(is_deleted = 0).order_by('ip')]
        h_queryset = HttpProxy.objects.filter(is_deleted = 0, whitelist_refers=None, blacklist_refers=None).order_by('proxy_domain_name')
        # no_strategy_objs = []
        # for obj in h_queryset:
        #     if not (obj.whitelist_refers.filter(is_deleted=0).exists() or obj.blacklist_refers.filter(is_deleted=0).exists()):
        #         no_strategy_objs.append(obj)
        self.response_data['proxies'] = [ p.proxy_domain_name for p in h_queryset]

    def add(self):
        obj, post_data = super().add()
        if obj is not None:
            obj.iplist.set(self.access_ip_objs)

    def edit(self):
        obj, post_data, pillar_attrs = super().edit()
        if obj is not None:
            obj.iplist.set(self.access_ip_objs)
