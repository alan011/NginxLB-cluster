#!/bin/bash

SELF_IP=$1
ACTION=$2
OTHER_ARGS=$3

function safe_rm(){
    if [ -f $1 ]; then
        mv $1 /tmp/`basename $1`.`date +'%s.%N'`
    fi
}

function check_params(){
    [ -z "$SELF_IP" ] && echo "ERROR: Parameter 'SELF_IP' master be given as \$1." && exit 1
    [ -z "$ACTION" ] && echo "ERROR: Parameter 'ACTION' master be given as \$2." && exit 1
    echo "===> ${ACTION}..."
    # echo "SELF_IP: ${SELF_IP}, ACTION: ${ACTION}, OTHER_ARGS: ${OTHER_ARGS}, WEB_MASTER: ${WEB_MASTER}, SET_HNAME: ${SET_HNAME}" && exit 1


    if [[ "$ACTION" =~ ^.*_config$ ]]; then
        if [ -z "$OTHER_ARGS" ]; then
            echo "ERROR: Parameter 'WEB_MASTER' master be given as \$3." && exit 1
        else
            WEB_MASTER=$OTHER_ARGS
        fi
    elif [ "$ACTION" == "set_hostname" ]; then
        if [ -z "$OTHER_ARGS" ]; then
            echo "ERROR: Parameter 'SET_HNAME' master be given as \$3." && exit 1
        else
            SET_HNAME=$OTHER_ARGS
        fi
    elif [ "$ACTION" == 'accept_keys' ]; then
        if [ -z "$OTHER_ARGS" ]; then
            echo "ERROR: Parameter 'MINION_KEYS' master be given as \$3." && exit 1
        else
            MINION_KEYS=$OTHER_ARGS
        fi
    fi
}

function install_packages(){
    yum install -y salt-master salt-minion
    [ $? -ne 0 ] && echo "ERROR: To install packages failed." && exit 1
    echo "Complete!"
}

function master_config(){
    wget -q http://$WEB_MASTER/scripts/configfiles/master -O /etc/salt/master
    [ $? -ne 0 ]  && exit 1
    echo "Complete!"
}

function minion_config(){
    wget -q http://$WEB_MASTER/scripts/configfiles/minion -O /etc/salt/minion
    [ $? -ne 0 ]  && exit 1
    echo `hostname` > /etc/salt/minion_id
    echo "Complete!"
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

function set_hostname() {
    hostname $SET_HNAME
    echo "NETWORKING=yes
HOSTNAME=$SET_HNAME" > /etc/sysconfig/network
    sed -i "/^${SELF_IP} ${SET_HNAME}$/ d" /etc/hosts
    echo "$SELF_IP $SET_HNAME" >> /etc/hosts
    echo "Complete!"
}

function sys_config() {
    if [ ! -f /etc/sysctl.conf_backup_by_nlb ]; then
        mv /etc/sysctl.conf /etc/sysctl.conf_backup_by_nlb
    fi
    wget -q http://${WEB_MASTER}/scripts/configfiles/sysctl.conf -O /etc/sysctl.conf
    if [ $? -ne 0 ]; then
        if [ -f /etc/sysctl.conf_backup_by_nlb ]; then
            safe_rm /etc/sysctl.conf
            mv /etc/sysctl.conf_backup_by_nlb /etc/sysctl.conf
        fi
        exit 1
    else
        sysctl -p /etc/sysctl.conf
        echo "Complete!"
    fi
}

function accept_keys() {
    salt-key -a ${MINION_KEYS} -y
    [ $? -ne 0 ] && exit 1
    echo "Complete!"
}

#--------------- main ------------------

check_params

echo "$ACTION" | egrep '^(install_packages|master_config|minion_config|start_master|start_minion|stop_master|stop_minion|set_hostname|sys_config|accept_keys)$' > /dev/null
[ $? -ne 0 ] && echo "ERROR: ACTION '$ACTION' not support!" && exit 1

$ACTION
