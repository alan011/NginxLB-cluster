#!/bin/bash

ACTION=$1

function check_params(){
    [ -z "$ACTION" ] && echo "ERROR: Parameter 'ACTION' master be given as \$1." && exit 1
    echo "===> ${ACTION}..."
}

function start_nginx(){
    /etc/init.d/nginx start
    [ $? -ne 0 ] && exit 1
    echo "Complete!"
}

function stop_nginx(){
    /etc/init.d/nginx stop
    [ $? -ne 0 ] && exit 1
    echo "Complete!"
}

function reload_nginx(){
    /etc/init.d/nginx reload
    [ $? -ne 0 ] && exit 1
    echo "Complete!"
}

function check_nginx_config(){
    /usr/sbin/nginx -t
    [ $? -ne 0 ] && exit 1
    echo "Complete!"
}

function nginx_status(){
    /etc/init.d/nginx status
    [ $? -ne 0 ] && exit 1
    exit 0
}

function start_master(){
    /etc/init.d/salt-master start
    [ $? -ne 0 ] && exit 1
    echo "Complete!"
}

function start_minion() {
    /etc/init.d/salt-minion start
    [ $? -ne 0 ] && exit 1
    echo "Complete!"
}

function stop_master() {
    /etc/init.d/salt-master stop
    [ $? -ne 0 ]  && exit 1
    echo "Complete!"
}

function stop_minion() {
    /etc/init.d/salt-minion stop
    [ $? -ne 0 ] && exit 1
    echo "Complete!"
}

#--------------- main ------------------

check_params

echo "$ACTION" | egrep '^(start_master|start_minion|stop_master|stop_minion|start_nginx|stop_nginx|reload_nginx|check_nginx_config|nginx_status)$' > /dev/null
[ $? -ne 0 ] && echo "ERROR: ACTION '$ACTION' not support!" && exit 1

$ACTION
