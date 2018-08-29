{%- for instance in pillar["whitelist"].itervalues() %}
{%- set white_list=instance["white_list"] %}
{%- set domain_name=instance["proxy_domain_name"] %}

{%- if instance.get('is_disabled') == '1' %}
/etc/nginx/luafiles/{{ domain_name }}.lua:
  file.absent
    #- watch_in:
    #  - service: nginx
{%- else %}
/etc/nginx/luafiles/{{ domain_name }}.lua:
  file.managed:
    - source: salt://whitelist/instance/templates/temp.example.com.lua
    - user: root
    - group: root
    - mode: 644
    - template: jinja
    - defaults:
      white_list: {{ white_list }}
    #- watch_in:
    #  - service: nginx
{%- endif %}

{%- endfor %}
