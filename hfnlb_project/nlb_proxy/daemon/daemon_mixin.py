import paramiko
from nlb_proxy.models import NLBConfig, ClusterMember, HttpProxy, TcpProxy, WhiteListStrategy, BlackListStrategy
from nlb_proxy.tools  import Logging

class DaemonMixin(object):
    model_to_module = {
       HttpProxy: "http_proxy",
       TcpProxy: "tcp_proxy",
       WhiteListStrategy: 'whitelist',
       BlackListStrategy: 'blacklist'
    }

class sshExecutorMixin(object):
    def __init__(self, log_file):
        self.log_file = log_file
        self.logger = None
        if self.log_file:
            self.logger = Logging(self.log_file)

    def getSetting(self):
        queryset = NLBConfig.objects.filter(name = 'initConfig')
        if queryset.exists():
            obj = queryset.get(name='initConfig')
            return obj.content
        else:
            self.logger.log('ERROR: server init setting data is not set properly!')

    def remoteConnect(self, hostIP, sysuser, syspasswd):
        ### ssh pre-settings
        client = paramiko.client.SSHClient()
        client.set_missing_host_key_policy(paramiko.client.AutoAddPolicy)
        client.load_system_host_keys()

        ### works begin
        self.logger.log("Trying to login to host: '%s'..." % hostIP)
        try:
            client.connect(hostIP, username=sysuser, password=syspasswd)
        except paramiko.ssh_exception.NoValidConnectionsError as e:
            self.logger.log("ERROR: %s" % str(e) )
            return None
        else:
            self.logger.log("Login to host '%s'... successfully, ready to run commands." % hostIP)
            return client

    def remoteRun(self, client, cmd):
        # print(cmd)
        stdin, stdout, stderr = client.exec_command(cmd, get_pty=True)
        for line in stdout:
            self.logger.log(line.strip('\n'))
        for line in stderr:
            self.logger.log(line.strip('\n'))
        return_code = stdout.channel.recv_exit_status()
        if return_code != 0:
            self.logger.log("ERROR: Command '%s' received error code: %d. Init-works aborted! " % (cmd, return_code))
        return return_code

    def remoteClose(self, ip, client):
        client.close()
        self.logger.log("Logout from host: '%s'!" % ip)

    def connectToMaster(self, sysuser, syspasswd):
        queryset = ClusterMember.objects.filter(role='MASTER', is_deleted=0)
        if queryset.exists():
            obj = queryset.get(role='MASTER')
            client = self.remoteConnect(obj.ip, sysuser, syspasswd)
            if client:
                return obj, client
        else:
            self.logger.log("ERROR: connectToMaster(): No available MASTER found!")
            return None, None
