from django.views.generic import View
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth import authenticate, login, logout
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required

import json, time

@method_decorator(csrf_exempt, name='dispatch')
class APILogin(View):
    def post(self, request, *args, **kwargs):
        action   = request.POST.get('action')
        if action == 'login':
            username = self.request.POST['username']
            password = self.request.POST['password']
            user = authenticate(username=username, password=password)
            if user is not None:
                if user.is_active:
                    if not self.request.POST.get('remember_me', None):
                        self.request.session.set_expiry(0)
                    login(self.request, user)
                    print('User %s login successfully!' % username)
                    return HttpResponse(json.dumps({'result':'LOGIN_SUCCESS'}), content_type='application/json')
                else:
                    return HttpResponse(json.dumps({'result':'NOT_ACTIVE','message':'用户未激活'}), content_type='application/json')
            else:
                return HttpResponse(json.dumps({'result':'LOGIN_FAILED', 'message':'用户名或密码不正确'}), content_type='application/json')
        else:
            return HttpResponse(json.dumps({'message':'ERROR: Bad Request.'}), status=400)
    def get(self, request):
        return HttpResponse(json.dumps({'message':'ERROR: Bad Request.'}), status=400)


@method_decorator(login_required, name='dispatch')
class APIUserInfo(View):
    def get(self, request, *args, **kwargs):
        user_info = { "username": request.user.username,
                    "realname": request.user.first_name,
                    "result":'SUCCESS',
                    }
        if not user_info["realname"]:
            user_info["realname"] = user_info["username"]

        return HttpResponse(json.dumps(user_info), content_type="application/json")

    def post(self, request):
        return HttpResponse("ERROR: Bad Request", status=400)
