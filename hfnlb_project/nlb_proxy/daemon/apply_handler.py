from geniusalt.operators import ModuleOperator, InstanceOperator, NodeOperator, RelationOperator, PushOperator
from nlb_proxy.models import HttpProxy, TcpProxy, ClusterMember, PushLog, WhiteListStrategy, BlackListStrategy
from nlb_proxy.tools import Logging
from django.utils import timezone
from .daemon_mixin import DaemonMixin

class ApplyHandler(DaemonMixin):
    httpStrategyModels = (WhiteListStrategy, BlackListStrategy, )

    def __init__(self, log_file=None):
        # self.apply_failed_objects = []
        self.instance_op = InstanceOperator(parameters={})
        self.push_op = PushOperator(parameters={})
        self.module_op = ModuleOperator(parameters={})
        self.relation_op = RelationOperator(parameters={})
        self.log_file = log_file
        self.logger = None
        if self.log_file:
            self.logger = Logging(self.log_file, 'ApplyHandler')

    def getInstance(self, instance):
        self.instance_op.parameters = {'name':instance}
        result = self.instance_op.show()
        if isinstance(result, dict):
            for instance_attr in result['data']:
                if instance_attr['name'] == instance:
                    return instance_attr

    def getNodes(self, filter=None):
        if filter is not None:
            queryset = ClusterMember.objects.filter(**filter)
        else:
            queryset = ClusterMember.objects.all()
        nodes = []
        for obj in queryset:
            nodes.append(obj.hostname)
        return nodes

    def getModulePillars(self, module):
        self.module_op.parameters = {'name':module}
        result = self.module_op.show()
        # print(result)
        if isinstance(result, dict):
            for module_attr in result['data']:
                if module_attr['name'] == module:
                    return result['data'][0]['pillar_required'] + result['data'][0]['pillar_optional']

    def logOperatorResult(self, result, obj=None, failed_list=None):
        if isinstance(result, dict):
            message_lines = result['message'].strip().split('\n')
            # print(message_lines)
            for line in message_lines:
                self.logger.log(line)
            if result['result'] != 'SUCCESS':
                if failed_list is not None and obj is not None:
                    failed_list.append(obj)
            return result
        else:
            self.logger.log(result)
            if failed_list is not None and obj is not None:
                failed_list.append(obj)

    def getUnapplied(self, model):
        return model.objects.filter(apply_stat=0,is_deleted=0)


    def makePillar(self, module, obj):
        instance, pillar = '',{}
        if module in ('http_proxy', 'tcp_proxy'):
            pillar_vars = self.getModulePillars(module)
            instance = "%s.%s" % (module,obj.app_name)
            pillar = {k:getattr(obj, k) for k in pillar_vars if getattr(obj, k)}
        elif module in ('whitelist', 'blacklist'):
            instance = '%s.%s' % (module,obj.strategy_name)
            pillar = {'proxy_domain_name':obj.proxy_belong.proxy_domain_name,
                    'iplist':'/'.join([ip_obj.ip for ip_obj in obj.iplist.filter(is_deleted = 0)]),
                    'is_disabled':obj.is_disabled,}
        return instance, pillar

    def apply(self, model):
        nodes = self.getNodes({'is_init':1, 'is_alive':1, 'is_deleted':0})
        if not nodes:
            self.logger.log('ERROR: No Nodes available to apply Instances!')
            return None

        queryset = self.getUnapplied(model)
        apply_failed_objects = []

        for obj in queryset:
            instance, pillar = self.makePillar(self.model_to_module[model], obj)
            # print(pillar)
            old_attrs = self.getInstance(instance)
            if old_attrs is None:
                self.logger.log("Trying to add new instance '%s'" % instance)
                instance_attrs = {'name': instance,
                                "module_belong":self.model_to_module[model],
                                "pillar":pillar.copy(),
                                }
                self.instance_op.parameters = instance_attrs
                self.logOperatorResult(self.instance_op.add(), obj, apply_failed_objects)
            else:
                self.logger.log("Trying to set pillar of instance '%s'" % instance)
                # print(pillar)
                # print(old_attrs['pillar'])
                for p in old_attrs['pillar']:
                    if p not in pillar:
                        self.instance_op.parameters = {'name':instance, 'pillar_name':p}
                        self.logger.log("Trying to delete pillar '%s' of instance '%s'" % (p, instance))
                        self.logOperatorResult(self.instance_op.pillarDel(), obj, apply_failed_objects)
                self.instance_op.parameters = {'name':instance,'pillar':pillar.copy()}
                self.logOperatorResult(self.instance_op.pillarSet(), obj, apply_failed_objects)

            ### Handle strategy instance's relationship with http instance.
            new_included = False
            if model in self.httpStrategyModels:
                http_proxy_instance = "%s.%s" % (self.model_to_module[HttpProxy],obj.proxy_belong.app_name)
                self.relation_op.parameters = {'instances': [http_proxy_instance],'included_instances': [instance]}
                check_result = self.relation_op.hasInclude()
                if isinstance(check_result, dict):
                    if check_result['check_result'] is False:
                        self.logOperatorResult(self.relation_op.include(), obj, apply_failed_objects)
                        if obj not in apply_failed_objects:
                            new_included = True
                else:
                    self.logger.log(check_result)

            ### push this instance to Nodes
            if obj not in apply_failed_objects:
                self.push_op.parameters = {'bind_instances':[instance], 'nodes':nodes}
                pushlog = {'push_time': timezone.now(),
                            'type':model.TYPE,
                            'target_id':obj.id,
                          }
                result = self.logOperatorResult(self.push_op.push(), obj, apply_failed_objects)
                if result:
                    pushlog['log_path'] = result['pushlog_path']
                else:
                    pushlog['message'] = 'ERROR: Push failed at this time and no logs returned.'

                log_obj = PushLog(**pushlog)
                try:
                    log_obj.save()
                except:
                    self.logger.log("ERROR: Trying to save PushLog object for app '%s' failed. Maybe some db related error occurred!" % instance)

        for obj in queryset:
            if obj in apply_failed_objects:
                obj.apply_stat = 2
            else:
                obj.apply_stat = 3
                obj.push_stat  = 1
                if model in self.httpStrategyModels and new_included is True:
                    obj.proxy_belong.apply_stat = 0
                    obj.proxy_belong.save()
            obj.save()

    def applyHandler(self):
        # print('Start applying works.')
        if self.logger is None:
            return "ERROR: This method requires that argument 'log_file' must be provided when you trying to init an 'ApplyHandler'."
        for model in self.model_to_module:
            self.apply(model)
