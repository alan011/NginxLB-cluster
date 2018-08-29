#!/usr/local/bin/python3
from nlb_proxy.models import NLBConfig, ClusterMember
from nlb_proxy.config import WEB_MASTER, WEB_MASTER_PORT, SALT_BIN
from nlb_proxy.tools  import Logging
from geniusalt.operators import RelationOperator
from .daemon_mixin import sshExecutorMixin, DaemonMixin
from os import popen
import yaml, json

class MinionHealthCheck(sshExecutorMixin, DaemonMixin):
    def __init__(self, log_path):
        super().__init__(log_path)
        self.logger.log_prefix = 'HealthCheck'
        self.queryset = ClusterMember.objects.filter(is_init=1)
        self.master_obj = self.findMaster()
        self.remote_script = 'http://%s:%s/scripts/service_check.sh' % (WEB_MASTER, WEB_MASTER_PORT)

    def yamlHandler(self, result):
        try:
            result_dict = yaml.load(result)
        except yaml.scanner.ScannerError as e:
            self.logger.log('ERROR: yaml.load(): '+str(e))
        else:
            if isinstance(result_dict, dict):
                return result_dict
            else:
                self.logger.log("ERROR: salt result not a dict: %s" % str(result_dict))

    def jsonHandler(self, result):
        try:
            result_dict = json.loads(result)
        except json.decoder.JSONDecodeError as e:
            self.logger.log('ERROR: json.loads(): ' +str(e))
        else:
            if isinstance(result_dict, dict):
                return result_dict
            else:
                self.logger.log("ERROR: salt result not a dict: %s" % str(result_dict))

    def findMaster(self):
        master_obj = None
        if self.queryset.exists():
            for obj in self.queryset:
                if obj.role == 'MASTER':
                    master_obj = obj
                    break
        else:
            self.logger.log('ERROR: No members found in your cluster.')
        if master_obj is None or master_obj.ip != WEB_MASTER:
            self.logger.log('ERROR: Master of your cluster is not set properly.')
            for obj in self.queryset:
                obj.is_alive = 4
                obj.save()

        return master_obj


    def execScriptOnMaster(self, queryset, script_args):
        exec_result = {}
        for obj in queryset:
            exec_result[obj] = False
            cmd = "%s --out json %s cmd.script %s %s" % (SALT_BIN,obj.hostname, self.remote_script, script_args )
            result_dict = self.jsonHandler(popen(cmd).read().strip())
            if result_dict:
                if isinstance(result_dict[obj.hostname], dict):
                    if result_dict[obj.hostname]['retcode'] == 0:
                        exec_result[obj] = True
                    else:
                        script_output = result_dict[obj.hostname]['stdout'] + result_dict[obj.hostname]['stderr']
                        self.logger.log(script_output.replace('\n', ';'))
                else:
                    self.logger.log("ERROR: Node '%s' return unexpect salt-returns: " + str(result_dict[obj.hostname]))
        return exec_result

    def saltHealthCheck(self):
        if not self.master_obj:
            return None

        healthy_obj = None
        for obj in self.queryset:
            if obj.is_alive == 1:
                healthy_obj = obj
                break

        ### Checking...
        check_result ={}
        for obj in self.queryset:
            check_result[obj] = False
            cmd = '%s --out json %s test.ping' % (SALT_BIN,obj.hostname)
            result_dict = self.jsonHandler(popen(cmd).read().strip())
            if result_dict and result_dict.get(obj.hostname) is True:
                check_result[obj] = True

        relation_op = RelationOperator(parameters={})  ### For member clone.
        members_need_clone = []
        for obj in check_result:
            if check_result[obj]:
                ### change member's status from unhealthy to healthy.
                if obj.is_alive != 1:
                    if healthy_obj is not None:
                        ### clone pillars of this obj from a healthy member and apply these pillars to member.
                        relation_op.parameters = {'nodes':[obj.hostname], 'clone_target':[healthy_obj.hostname],'push':True}
                        result = relation_op.clone()
                        print(result)
                        if isinstance(result, dict):
                            if result['result'] == 'SUCCESS':
                                obj.is_alive = 1
                                obj.save()
                                self.logger.log("Cluster member '%s' up." % obj.hostname)
                            self.logger.log(result['message'])
                        else:
                            self.logger.log(result)
                else:
                    obj.is_alive = 1
                    obj.save()
            ### change member's status from healthy to unhealthy.
            elif obj.is_alive == 1:
                obj.is_alive = 2
                obj.save()
                self.logger.log("ERROR: Cluster member '%s' down!" % obj.hostname)

    def nginxHealthCheck(self):
        if not self.master_obj:
            return None
        queryset = self.queryset.filter(is_alive__in = [1,3])
        check_result = self.execScriptOnMaster(queryset, 'nginx_status')

        for obj in check_result:
            if check_result[obj]:
                if obj.is_alive == 3:  ### Change status from 'nginx unhealthy' to 'healthy'.
                    obj.is_alive == 1
                    obj.save()
            else:
                if obj.is_alive == 1:  ### Change status from 'healthy' to 'nginx unhealthy'.
                    obj.is_alive = 3
                    obj.save()
    def reloadHealthyNginx(self):
        if not self.master_obj:
            return None
        queryset = self.queryset.filter(is_alive=1)
        app_objs = []
        for model in self.model_to_module:
            app_queryset = model.objects.filter(is_deleted=0, apply_stat=3)
            for app in app_queryset:
                app_objs.append(app)

        ### To reload healthy nginx.
        if app_objs:
            reload_result = self.execScriptOnMaster(queryset, 'reload_nginx')
            reload_failed = []
            for obj in reload_result:
                if reload_result[obj] is False:
                    reload_faield.append(obj.hostname)
            if reload_failed:
                obj.need_reload = 1
                obj.save()
                self.logger.log('ERROR: Some members to reload nginx failed: %s' % str(reload_failed))
            else:
                self.logger.log('To reload nginx succeeded on all alive members: %s' % str([obj.hostname for obj in queryset]))
            for app_obj in app_objs:
                app_obj.apply_stat = 1
                app_obj.save()

    def healthCheck(self):
        self.saltHealthCheck()
        self.nginxHealthCheck()
        self.reloadHealthyNginx()
