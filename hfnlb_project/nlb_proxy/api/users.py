from django.views.generic import View
from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User

import re,json

@method_decorator(csrf_exempt, name='dispatch')
@method_decorator(login_required, name='dispatch')
class APIUsers(View):
    def __init__(self, *args, **kwargs):
        self.response_data = {'result':'SUCCESS','message':''}
        self.status = 200
        super().__init__(*args, **kwargs)

    def dataVerify(self):
        fields_required = ['username','passwd']
        fields_optional = ['email','realname']

        form_data = {k:v.strip() for k,v in self.post_data.items() if k in fields_required + fields_optional}

        ### Check fields required.
        for field in fields_required:
            if field not in form_data:
                return "错误：请提供字段'%s'!" % field
        return form_data

    def checkName(self, checkExist=False):
        name = self.post_data.get('username')
        queryset = User.objects.filter(username = name)
        if not queryset.exists():
            if not checkExist:
                self.response_data.update({'result':'FAILED', 'message':"错误：用户'%s'不存在！" % name})
                self.status = 404
            return None
        else:
            return queryset.get(username = name)

    def saveObject(self, obj):
        try:
            obj.save()
        except:
            self.response_data.update({'result':'FAILED', 'message':"错误：数据库错误，请联系管理员！"})
            self.status = 500

    def add(self):
        data = self.dataVerify()
        if isinstance(data, str):
            self.response_data.update({'result':'FAILED', 'message':data})
            self.status = 400
        else:
            if self.checkName(checkExist=True):
                self.response_data.update({'result':'FAILED', 'message':"错误：用户'%s'已存在，请使用其他用户ID！" % data['username']})
                self.status = 400
            else:
                user = User.objects.create_user(data['username'],email=data['email'],password=data['passwd'],first_name=data['realname'])
                self.saveObject(user)

    def delete(self):
        user = self.checkName()
        if user:
            user.delete()

    def edit(self):
        user = self.checkName()
        data = self.dataVerify()
        change = False
        if user:
            if data.get('realname') and user.first_name != data['realname']:
                user.first_name = data['realname']
                change = True
            if data.get('email') and user.email != data['email']:
                user.email = data['email']
                change = True
        if change:
            self.saveObject(user)

    def resetPasswd(self):
        user = self.checkName()
        if user:
            passwd = self.post_data.get('newPasswd')
            if passwd is not None:
                user.set_password(str(passwd).strip())
                self.saveObject(user)
            else:
                self.response_data.update({'result':'FAILED', 'message':"密码重置错误：请提供一个新密码！"})
                self.status = 400

    def get(self, request, *args, **kwargs):
        queryset = User.objects.all()
        data = []
        for user in queryset:
            attr = {'username':user.username,
                    'email':user.email,
                    'realname':user.first_name,
                    'group':'admin',
                 }
            data.append(attr)
        self.response_data['data'] = data
        self.response_data['groups'] = [{'lable': '管理员', 'value': 'admin'},
                                       ]
        return HttpResponse(json.dumps(self.response_data),content_type='application/json',status=self.status)


    def post(self, request, *args, **kwargs):
        legal_action = ['add', 'delete', 'edit','resetPasswd']
        self.post_data = {k:v.strip() for k,v in request.POST.items()}
        # print(self.post_data)

        action = self.post_data.get('action')
        if action in legal_action:
            getattr(self, action)()
        else:
            self.response_data.update({'result':'FAILED','message':"ERROR: action '%s' not support." % action})
            self.status == 400

        return HttpResponse(json.dumps(self.response_data),content_type='application/json',status=self.status)
