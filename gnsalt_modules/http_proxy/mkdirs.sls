httpproxy_config_dir:
    file.directory:
        - name: /etc/nginx/conf.d
        - user: root
        - group: root
        - mode: 755
        - makedirs: True
