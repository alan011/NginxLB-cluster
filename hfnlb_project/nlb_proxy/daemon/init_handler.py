from nlb_proxy.models import ClusterMember
from nlb_proxy.config import WEB_MASTER, WEB_MASTER_PORT
from .daemon_mixin import sshExecutorMixin

class ServerInitHandler(sshExecutorMixin):
    """
    To define what works should be done when to init a master or a minion.
    """

    def __init__(self, log_file):
        super().__init__(log_file)
        self.logger.log_prefix = 'ServerInit'

    def getServers(self):
        return ClusterMember.objects.exclude(is_init=1)

    def getHostname(self, ip, client):
        stdin, stdout, stderr = client.exec_command('hostname', get_pty=True)
        if stdout.channel.recv_exit_status() != 0:
            self.logger.log("ERROR: ServerInitHandler.getHostname(): To get hostname of ip '%s' failed!" % ip)
            return None
        return ''.join([line.strip() for line in stdout])

    def serverInit(self):
        members = self.getServers()

        initSetting = self.getSetting()
        if not initSetting:
            return None

        # print("Start server init works. Ip list: %s" % str([obj.ip for obj in members]))
        success_members = []
        for obj in members:
            works = []
            works.append('wget -q http://%s:%s/scripts/nlb_init.sh -O /tmp/nlb_init.sh' % (WEB_MASTER, WEB_MASTER_PORT))
            works.append('sudo /bin/bash /tmp/nlb_init.sh %s install_packages' % obj.ip)
            if initSetting['sethostname'] == 'Y':
                hostname = "%s-%s" % (initSetting['hostnameprefix'],obj.id)
                works.append('sudo /bin/bash /tmp/nlb_init.sh %s set_hostname %s' % (obj.ip,hostname))
            works.append('sudo /bin/bash /tmp/nlb_init.sh %s sys_config %s' % (obj.ip,WEB_MASTER))
            works.append('sudo /bin/bash /tmp/nlb_init.sh %s master_config %s' % (obj.ip,WEB_MASTER))
            works.append('sudo /bin/bash /tmp/nlb_init.sh %s minion_config %s' % (obj.ip,WEB_MASTER))
            if obj.role == 'MASTER':
                works.append('sudo /bin/bash /tmp/nlb_init.sh %s start_master' % obj.ip)
            works.append('sudo /bin/bash /tmp/nlb_init.sh %s start_minion' % obj.ip)

            ### To do the works
            client = self.remoteConnect(obj.ip, initSetting['sysuser'], initSetting['syspasswd'])
            if client is not None:
                success = True
                for step in works:
                    return_code = self.remoteRun(client, step)
                    if return_code != 0:
                        success = False
                        break
                if success:
                    host_name = self.getHostname(obj.ip, client)
                    if host_name:
                        obj.hostname = host_name
                        obj.is_init = 1
                        obj.save()
                        success_members.append(obj)

                self.remoteClose(obj.ip, client)

    def acceptKeys(self):
        """ Tell master to accept new minion-keys """
        # print('Start keys accepting works.')
        success_members = ClusterMember.objects.filter(is_init=1, is_alive=0)
        if success_members.exists():
            initSetting = self.getSetting()
            if not initSetting:
                return None
            master_obj, master_ssh_client = self.connectToMaster(initSetting['sysuser'],initSetting['syspasswd'])
            if master_obj and master_obj.is_init == 1:
                return_code = self.remoteRun(master_ssh_client, 'sudo /bin/bash /tmp/nlb_init.sh %s accept_keys %s' % (master_obj.ip, ','.join([obj.hostname for obj in success_members])))
                if return_code == 0:
                    for obj in success_members:
                        obj.is_alive = 1
                        obj.save()
