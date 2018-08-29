from django.views.generic import View
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q

from nlb_proxy.tools import validateIP
from nlb_proxy.models import AccessControlIPList, WhiteListStrategy
from .common import APIMixin

import re,json,os

@method_decorator(csrf_exempt, name='dispatch')
@method_decorator(login_required, name='dispatch')
class IPListView(View, APIMixin):
    model = AccessControlIPList
    fields_required = ['ip']
    fields_optional = ['description']

    def dataVerify(self):
        form_data = {k:v.strip() for k,v in self.post_data.items() if k in self.fields_required + self.fields_optional}

        ### Check fields required.
        for field in self.fields_required:
            if field not in form_data:
                return "ERROR: Field '%s' is required!" % field

        ### Check 'ip'
        if not validateIP(form_data['ip']):
            return "ERROR: Illegal value detected for field 'ip': '%s'" % form_data['ip']

        return form_data

    def checkExists(self, verified_data):
        filter_list =[{'ip':verified_data['ip']},
                     ]
        return self.checkExistsWithFilterList(filter_list)

    def normalSearch(self, search_value):
        return self.model.objects.filter(is_deleted = 0).filter(Q(ip__icontains= search_value )|Q(description__icontains= search_value )|Q(add_user__username__icontains= search_value ))

    def searchData(self):
        return self.normalSearch(self.request.GET.get('search_value')).order_by('-id')

    def makeDataList(self, queryset):
        data = []
        for obj in queryset:
            attrs = {'id': obj.id,
                    'ip': obj.ip,
                    'whitelists':[ wl.strategy_name for wl in obj.whitelist_refers.filter(is_deleted=0)],
                    'description': obj.description,
                    'add_time': obj.add_time.strftime('%F %T'),
                    'add_user': obj.add_user.username,
                    }
            # print(attrs['whitelists'])

            data.append(attrs)
        return data
