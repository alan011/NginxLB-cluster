from django.conf.urls import url
from geniusalt.api.api_ingress import GeniusaltIngress
from geniusalt.views import checkView

app_name = 'geniusalt'
urlpatterns =  [ url(r'^api/v1/ingress',GeniusaltIngress.as_view(), name='GeniusaltIngress'),
                 url(r'^check', checkView),
                        ]
