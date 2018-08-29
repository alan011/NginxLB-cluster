proxy_log_dir:
    file.directory:
        - name: /data1/logs/
        - user: root
        - group: root
        - mode: 755
        - makedirs: True
        - require:
            - pkg: openresty
