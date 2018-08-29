from django.conf.urls import url
from nlb_proxy.api import HTTPProxyView, TCPProxyView, APILogin, APIUserInfo, APIUsers, NLBCluster, IPListView, WhitelistView, BlacklistView

app_name = 'proxy'
urlpatterns =  [ url(r'^api/v1/httpproxy$',HTTPProxyView.as_view(), name='HTTPProxyView'),
                 url(r'^api/v1/tcpproxy$',TCPProxyView.as_view(), name='TCPProxyView'),
                 url(r'^api/v1/login$',APILogin.as_view(), name='APILogin'),
                 url(r'^api/v1/userinfo$', APIUserInfo.as_view(), name='APIUserInfo'),
                 url(r'^api/v1/users$', APIUsers.as_view(), name='APIUsers'),
                 url(r'^api/v1/cluster$', NLBCluster.as_view(), name='NLBCluster'),
                 url(r'^api/v1/iplist$', IPListView.as_view(), name='IPListView'),
                 url(r'^api/v1/whitelist$', WhitelistView.as_view(), name='WhitelistView'),
                 url(r'^api/v1/blacklist$', BlacklistView.as_view(), name='BlacklistView'),
               ]
