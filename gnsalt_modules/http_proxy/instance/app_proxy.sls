{%- for instance in pillar["http_proxy"].itervalues() %}
{%- set proxy_domain_name=instance["proxy_domain_name"] %}
{%- set app_name=instance["app_name"] %}
{%- set app_servers=instance["app_servers"].split('/') %}
{%- set app_port=instance["app_port"] %}

{%- if instance.get("other_domain_names") %}
{%- set other_domain_names=instance["other_domain_names"].split('/') %}
{%- else %}
{%- set other_domain_names=[] %}
{%- endif %}

{%- if instance.get("proxy_listen_ports") %}
{%- set proxy_listen_ports=instance["proxy_listen_ports"].split('/') %}
{%- else %}
{%- set proxy_listen_ports=[] %}
{%- endif %}

{%- if instance.get("app_servers_backup") %}
{%- set app_servers_backup=instance["app_servers_backup"].split('/') %}
{%- else %}
{%- set app_servers_backup=[] %}
{%- endif %}

{%- set tmp={'has_white_list':'N'} %}
{%- if instance.get("__include__") %}
{%- for ii in instance["__include__"].keys() %}
{%- if ii.split('.')[0] == 'whitelist' %}
{%- if tmp.update({'has_white_list':'Y'}) %}{%- endif%}
{%- endif %}
{%- endfor %}
{%- endif %}

{%- if instance.get('is_disabled') == '1' %}
/etc/nginx/conf.d/{{ proxy_domain_name }}.conf:
  file.absent
    #- watch_in:
    #  - service: nginx
{%- else %}
/etc/nginx/conf.d/{{ proxy_domain_name }}.conf:
  file.managed:
    - source: salt://http_proxy/instance/templates/temp.http_proxy.conf
    - user: root
    - group: root
    - mode: 644
    - template: jinja
    - defaults:
      instance_name: http_proxy_for_{{ app_name }}
      domain_name: {{ proxy_domain_name }}
      app_port: {{ app_port }}
      app_servers: {{ app_servers }}
      proxy_listen_ports: {{ proxy_listen_ports }}
      other_domain_names: {{ other_domain_names }}
      backup_servers: {{ app_servers_backup }}
      has_white_list: {{ tmp.has_white_list }}

    #- watch_in:
    #  - service: nginx
{%- endif %}
{% endfor %}
