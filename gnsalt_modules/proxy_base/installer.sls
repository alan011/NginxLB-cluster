### install openresty package ###
openresty_for_proxy:
    pkg.installed:
        - name: openresty
    service.enabled:
        - name: nginx
    #service.running:
    #    - name: nginx
    #    - enable: True  #Start this service at system boot time.
    #    - reload: True
    #    - watch:
    #        - pkg: openresty

logrotate_for_proxy:
    file.managed:
        - name: /etc/logrotate.d/nginx
        - source: salt://proxy_base/files/nginx_for_logrotate
        - user: root
        - group: root
        - mode: 644

/etc/nginx/nginx.conf:
  file.managed:
    - source: salt://proxy_base/files/nginx.conf
    - user: root
    - group: root
    - mode: 644
    #- watch_in:
    #    - service: nginx
