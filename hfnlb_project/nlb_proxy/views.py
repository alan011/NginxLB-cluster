from django.http import HttpResponse, HttpResponseRedirect
from django.views.generic import View
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.contrib.auth import logout
from django.http import FileResponse
from django.conf import settings

from nlb_proxy.tools import static_render

import os

@method_decorator(login_required, name='dispatch')
class MyIndex(View):
    template_name = 'index_used.html'

    def get(self, request, *args, **kwargs):
        return HttpResponse(static_render(self.template_name))

class MyLogin(View):
    template_name = 'login/index_login.html'
    def get(self, request, *args, **kwargs):
        return HttpResponse(static_render(self.template_name))

class MyLogout(View):
    def get(self, request, *args, **kwargs):
        logout(request)
        return HttpResponseRedirect('/login/')

class ScriptServer(View):
    def get(self, request, *args, **kwargs):
        response = FileResponse(open(os.path.join(settings.BASE_DIR,'nlb_proxy/scripts/%s' % kwargs['filename']), 'rb'), content_type='application/force-download')
        response['Content-Disposition'] = 'attachment; filename=%s'  % os.path.basename(kwargs['filename'])
        return response
