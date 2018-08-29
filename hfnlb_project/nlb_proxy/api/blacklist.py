from django.views.generic import View
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt

from nlb_proxy.models import BlackListStrategy
from .common import APIStrategySaltPushMixin

@method_decorator(csrf_exempt, name='dispatch')
@method_decorator(login_required, name='dispatch')
class BlacklistView(View, APIStrategySaltPushMixin):
    model = BlackListStrategy
