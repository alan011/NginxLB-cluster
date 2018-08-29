{%- for instance in pillar["tcp_proxy"].itervalues() %}
{%- set app_name=instance["app_name"] %}
{%- set app_servers=instance["app_servers"].split('/') %}
{%- set app_port=instance["app_port"] %}

{%- if instance.get("other_domain_names") %}
{%- set other_domain_names=instance["other_domain_names"].split('/') %}
{%- else %}
{%- set other_domain_names=[] %}
{%- endif %}

{%- if instance.get("proxy_port") %}
{%- set proxy_port=instance["proxy_port"] %}
{%- else %}
{%- set proxy_port=app_port %}
{%- endif %}

{%- if instance.get("app_servers_backup") %}
{%- set app_servers_backup=instance["app_servers_backup"].split('/') %}
{%- else %}
{%- set app_servers_backup=[] %}
{%- endif %}

{%- if instance.get("is_disabled") %}
{%- set is_disabled=instance["is_disabled"] %}
{%- else %}
{%- set is_disabled='0' %}
{%- endif %}

{%- if is_disabled == '1' %}
/etc/nginx/stream.d/{{ app_name }}.tcp_proxy.conf:
  file.absent
    #- watch_in:
    #  - service: nginx
{%- else %}
/etc/nginx/stream.d/{{ app_name }}.tcp_proxy.conf:
  file.managed:
    - source: salt://tcp_proxy/instance/templates/temp.tcp_proxy.conf
    - user: root
    - group: root
    - mode: 644
    - template: jinja
    - defaults:
      instance_name: tcp_proxy_for_{{ app_name }}
      app_port: {{ app_port }}
      app_servers: {{ app_servers }}
      backup_servers: {{ app_servers_backup }}
      proxy_port: {{ proxy_port }}
    #- watch_in:
    #  - service: nginx
{%- endif %}
{% endfor %}
