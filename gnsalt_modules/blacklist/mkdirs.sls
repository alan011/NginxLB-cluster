whitelist_config_dir:
    file.directory:
        - name: /etc/nginx/luafiles
        - user: root
        - group: root
        - mode: 755
        - makedirs: True
