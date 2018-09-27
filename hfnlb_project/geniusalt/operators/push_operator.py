from geniusalt.models import Node, Instance, Module
from geniusalt.config import LOG_PATH
from .common import Operator

from threading import Thread
import os, sys, time, json, re


class SimulPush(Thread):
    def __init__(self, node_name, pillar):
        self.node_name=node_name
        self.pillar = pillar
        self.push_result=None
        self.log_path = None
        super(SimulPush, self).__init__()

    def run(self):
        self.push_result, self.log_path = self.pushOneNode()

    def pushOneNode(self):
        ### prepare log references.
        log_dir = os.path.join(LOG_PATH, self.node_name)
        if not os.path.isdir(log_dir):
            os.makedirs(log_dir)

        push_time = time.strftime('%Y-%m-%d_%H%M%S',time.localtime(time.time()))
        log_path = os.path.join(log_dir, 'push_at_%s.log' % (push_time,))
        log_path_f = open(log_path,'a')

        ### run salt push by assigning module name and pillar dict.
        cmd_line = 'salt %s state.sls %s %s' % (self.node_name, ','.join(list(self.pillar.keys())), 'pillar=\''+json.dumps(self.pillar)+'\'')
        # print("\n===> Saltstack: " + cmd_line)

        ### write push log
        log_ret = []
        log_f = os.popen(cmd_line)
        while True:
            log_line = log_f.readline()
            if log_line == '':
                break
            log_path_f.write(log_line)
            # print(log_line,end='')
            log_ret.append(log_line.rstrip())

        log_path_f.close()

        return log_ret, log_path



class PushOperator(Operator):
    fields_defination = {'nodes': {'value_type' : list,
                                  'item_type': 'object_name_list',
                                  'item_model': Node},

                         'bind_modules': {'value_type': list,
                                             'item_type': 'object_name_list',
                                             'item_model': Module},

                         'bind_instances': {'value_type': list,
                                             'item_type': 'object_name_list',
                                             'item_model': Instance},
                         'longTerms':      {'value_type': list,
                                            'item_type': 'choices',
                                            'item_choices':['--only-module', '--checkself']},

                        }
    def checkPushLog(self):
        pushlog = self.operator_return.get('pushlog')
        if pushlog:
            succeeded_nodes = []
            failed_nodes = []
            for n_name in pushlog:
                logs = '\n'.join(pushlog[n_name])
                # print(logs)
                if re.search('-+\nSucceeded:\s+\d+(\s+\(changed=\d+\))?\nFailed:\s+0\n-+', logs):
                    succeeded_nodes.append(n_name)
                else:
                    failed_nodes.append(n_name)
            self.operator_return['message'] = "Push finished, succeeded Nodes: %s, failed nodes: %s" % (', '.join(succeeded_nodes), ', '.join(failed_nodes))
            if failed_nodes:
                self.operator_return['result'] = 'FAILED'

    def push(self):
        """
        To push Module or Instance to Nodes. This makes the real installation for a real host.
        """
        fields_required, fields_optional = ['nodes'], ['bind_modules', 'bind_instances', 'longTerms']

        ### To validate data in self.parameters.
        validate_result = self.dataValidating(fields_required, fields_optional)
        if not isinstance(validate_result, dict):
            return validate_result

        ### To bind Modules or Instances to Nodes first.
        bind_modules, bind_instances = [],[]
        if validate_result.get('bind_modules'):
            bind_modules = validate_result['bind_modules']
        if validate_result.get('bind_instances'):
            bind_instances = validate_result['bind_instances']
            for i_obj in bind_instances:
                bind_modules.append(i_obj.module_belong)
        for n_obj in validate_result['nodes']:
            if bind_modules:
                n_obj.bind_modules.add(*bind_modules)
            if bind_instances:
                n_obj.bind_instances.add(*bind_instances)
            n_obj.save()

        ### To check locked objects:
        for n in validate_result['nodes']:
            if n.is_lock != 0:
                return "ERROR: Push action aborted because Node '%s' has been locked." % n.name
        if validate_result.get('bind_modules'):
            for m in validate_result['bind_modules']:
                if m.lock_count != 0:
                    return "ERROR: Push action aborted because Module '%s' has been locked." % m.name
        if validate_result.get('bind_instances'):
            for i in validate_result['bind_instances']:
                if i.is_lock != 0:
                    return "ERROR: Push action aborted because Instance '%s' has been locked." % m.name

        ### To make pillar dict for each node.
        pillar_total = {}
        for n in validate_result['nodes']:
            bind_pillar = n.pillar()
            pillar_total[n.name] = {}

            ### If Module or Instance is specified, use the specified pillar, not all the pillars installed for this Node.
            if validate_result.get('bind_modules'):
                if self.parameters.get('longTerms') and '--only-module' in self.parameters['longTerms']:
                    if validate_result.get('bind_instances'):
                        return "ERROR: Instance object should not be specified with longTerms '--only-module'."
                    ### To fill pillar with module name, without only instances.
                    for m in validate_result['bind_modules']:
                        pillar_total[n.name][m.name] = {}
                else:
                    ### To fill pillar with module name and its all instances installed on this node.
                    for m in validate_result['bind_modules']:
                        pillar_total[n.name][m.name] = bind_pillar[m.name]
            if validate_result.get('bind_instances'):
                if self.parameters.get('longTerms') and '--only-module' in self.parameters['longTerms']:
                    return "ERROR: Instance object should not be specified with longTerms '--only-module'."
                for i in validate_result['bind_instances']:
                    if i.module_belong.name not in pillar_total[n.name]:
                        pillar_total[n.name][i.module_belong.name] = {}
                    pillar_total[n.name][i.module_belong.name][i.name] = bind_pillar[i.module_belong.name][i.name]
            ### If no Module or Instance specified, use all the pillars installed for this node.
            if pillar_total[n.name] == {}:
                pillar_total[n.name] = bind_pillar

        ### To push objects to real hosts in multi-threading.
        thread_pool = {}
        push_log = {}
        push_log_path = {}
        for n in validate_result['nodes']:
            if not pillar_total[n.name]:
                push_log[n.name] = ["Pushing ignored for this Node '%s' because no pillar installed." % n.name]
            else:
                thread_pool[n.name] = SimulPush(n.name, pillar_total[n.name])
                thread_pool[n.name].start()
        for n_name in thread_pool:
            thread_pool[n_name].join()
            push_log[n_name] = thread_pool[n_name].push_result
            push_log_path[n_name] = thread_pool[n_name].log_path

        self.operator_return['pushlog'] = push_log
        self.operator_return['pushlog_path'] = push_log_path
        self.checkPushLog()
        return self.operator_return
