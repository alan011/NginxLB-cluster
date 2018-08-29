dyups_api_conf:
  file.managed:
    - name: /etc/nginx/conf.d/dyups.conf
    - source: salt://proxy_base/files/dyups.conf
    - user: root
    - group: root
    - mode: 644
    #- watch_in:
    #  - service: nginx
