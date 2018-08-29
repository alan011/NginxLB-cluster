from geniusalt.models import Node, Instance, Module, IncludeRelationship
from .common import Operator
from .push_operator import PushOperator

class RelationOperator(Operator):
    fields_defination = {'nodes': {'value_type' : list,
                                  'item_type': 'object_name_list',
                                  'item_model': Node},

                         'instances': {'value_type' : list,
                                      'item_type': 'object_name_list',
                                      'item_model': Instance},

                         'bind_modules': {'value_type': list,
                                             'item_type': 'object_name_list',
                                             'item_model': Module},

                         'bind_instances': {'value_type': list,
                                             'item_type': 'object_name_list',
                                             'item_model': Instance},

                         'included_instances': {'value_type': list,
                                             'item_type': 'object_name_list',
                                             'item_model': Instance},
                         'clone_target': {'value_type': list,
                                            'item_type': 'object_name_list',
                                            'item_model': Node},
                         'push': {'value_type': 'choices',
                                  'value_choices':[True, False]}
                        }
    def bind(self):
        """
        To bind Module or pillar of Instance to a Node. Only bind in DB, not really to install objects for a real host.
        """
        fields_required, fields_optional = ['nodes'], ['bind_modules', 'bind_instances']

        ### To validate data in self.parameters.
        validate_result = self.dataValidating(fields_required, fields_optional)
        if not isinstance(validate_result, dict):
            return validate_result

        ### To get objects.
        bind_modules, bind_instances = [], []
        if validate_result.get('bind_modules'):
            bind_modules = validate_result['bind_modules']
        if validate_result.get('bind_instances'):
            bind_instances = validate_result['bind_instances']
            for i_obj in bind_instances:
                if i_obj.module_belong not in bind_modules:
                    bind_modules.append(i_obj.module_belong)
        if not (bind_modules or bind_instances):
            return "ERROR: 'bind_modules' or 'bind_instances' is required."

        ### To set nodes.
        for n_obj in validate_result['nodes']:
            if bind_modules:
                n_obj.bind_modules.add(*bind_modules)
            if bind_instances:
                n_obj.bind_instances.add(*bind_instances)

            n_obj.save()

        self.operator_return['message'] = "To Bind objects %s to Nodes %s succeed.\n" % (str([o.name for o in bind_modules + bind_instances]), str(self.parameters['nodes']))
        return self.operator_return

    def unbind(self):
        """
        To unbind Module or pillar of Instance from a Node.
        """
        fields_required, fields_optional = ['nodes'], ['bind_modules', 'bind_instances']

        ### To validate data in self.parameters.
        validate_result = self.dataValidating(fields_required, fields_optional)
        if not isinstance(validate_result, dict):
            return validate_result

        ### To get objects.
        bind_modules = []
        bind_instances = []
        if validate_result.get('bind_modules'):
            bind_modules = validate_result['bind_modules']
        if validate_result.get('bind_instances'):
            bind_instances = validate_result['bind_instances']
        if not (bind_modules or bind_instances):
            return "ERROR: 'bind_modules' or 'bind_instances' is required."

        ### To set nodes.
        for n_obj in validate_result['nodes']:
            if bind_modules:
                n_obj.bind_modules.remove(*bind_modules)
            if bind_instances:
                n_obj.bind_instances.remove(*bind_instances)

            n_obj.save()

        self.operator_return['message'] = "To Unbind objects %s from Nodes %s succeed\n" % (str([o.name for o in bind_modules + bind_instances]), str(self.parameters['nodes']))
        return self.operator_return

    def include(self):
        """
        To set Instance objects to include other Instance object.
        """
        fields_required, fields_optional = ['instances', 'included_instances'], []

        ### To validate data in self.parameters.
        validate_result = self.dataValidating(fields_required, fields_optional)
        if not isinstance(validate_result, dict):
            return validate_result

        ### To check instances.
        for i_obj in validate_result['instances']:
            if i_obj in validate_result['included_instances']:
                return "ERROR: Instance obj '%s' cannot include itself" % i_obj.name

        ### To set relationship.
        for i_obj in validate_result['instances']:
            r_queryset =IncludeRelationship.objects.filter(r_instance=i_obj)
            if r_queryset.exists():
                r_obj = r_queryset.get(r_instance=i_obj)
            else:
                r_obj = IncludeRelationship(r_instance=i_obj)
                r_obj.save()

            for ii_obj in validate_result['included_instances']:
                r_obj.r_included.add(ii_obj)
            r_obj.save()

        self.operator_return['message'] = "To set instances %s to include other instances %s succeed\n" % (str(self.parameters['instances']), str(self.parameters['included_instances']))
        return self.operator_return

    def exclude(self):
        """
        To set Instance objects to exclude other Instance object.
        """
        fields_required, fields_optional = ['instances', 'included_instances'], []

        ### To validate data in self.parameters.
        validate_result = self.dataValidating(fields_required, fields_optional)
        if not isinstance(validate_result, dict):
            return validate_result

        ### To check instances.
        for i_obj in validate_result['instances']:
            if i_obj in validate_result['included_instances']:
                return "ERROR: Instance obj '%s' cannot exclude itself" % i_obj.name

        ### To set nodes.
        for i_obj in validate_result['instances']:
            r_queryset =IncludeRelationship.objects.filter(r_instance=i_obj)
            if r_queryset.exists():
                r_obj = r_queryset.get(r_instance=i_obj)
                for ii_obj in validate_result['included_instances']:
                    r_obj.r_included.remove(ii_obj)
                r_obj.save()

        self.operator_return['message'] = "To set instances %s to exclude other instances %s succeed\n" % (str(self.parameters['instances']), str(self.parameters['included_instances']))
        return self.operator_return

    def hasInclude(self):
        """
        List of parameters 'instances' and 'included_instances' must only contain one item.
        """
        fields_required, fields_optional = ['instances', 'included_instances'], []

        ### To validate data in self.parameters.
        validate_result = self.dataValidating(fields_required, fields_optional)
        if not isinstance(validate_result, dict):
            return validate_result

        ### To check relationship.
        included = False
        if len(validate_result['instances']) == 1 and len(validate_result['included_instances']) == 1:
            i_obj = validate_result['instances'][0]
            ii_obj = validate_result['included_instances'][0]
            r_queryset =IncludeRelationship.objects.filter(r_instance=i_obj)
            if r_queryset.exists():
                r_obj = r_queryset.get(r_instance=i_obj)
                if ii_obj in r_obj.r_included.all():
                    included = True
        else:
            return "ERROR: Multiple instances are not supported for hasInclude(). Please give single value for parameter 'instances' and 'included_instances'."

        if included:
            self.operator_return['message'] = "Instance '%s' did include instance '%s'.\n" % (i_obj.name, ii_obj.name)
        else:
            self.operator_return['message'] = "Instance '%s' did not include instance '%s'!\n" % (i_obj.name, ii_obj.name)
        self.operator_return['check_result'] = included

    def clone(self):
        """
        To clone node's pillars from 'clone_target' to 'nodes'. This will clear any pillars on 'nodes'.
        """
        fields_required, fields_optional = ['nodes', 'clone_target'], ['push']

        ### To validate data in self.parameters.
        validate_result = self.dataValidating(fields_required, fields_optional)
        if not isinstance(validate_result, dict):
            return validate_result

        ### check nodes.
        if len(validate_result['clone_target']) == 1:
            target_node = validate_result['clone_target'][0]
            for node in validate_result['nodes']:
                node.bind_modules.set(target_node.bind_modules.all())
                node.bind_instances.set(target_node.bind_instances.all())
            self.operator_return['message'] = "Nodes '%s' cloned from target node '%s' successfully!\n" % (self.parameters['nodes'], target_node.name)
            if validate_result.get('push') is True:
                self.operator_return['message'] += 'Trying to push nodes: %s' % self.parameters['nodes']
                push_op = PushOperator(parameters={'nodes':self.parameters['nodes']})
                print(push_op.parameters)
                push_result = push_op.push()
                if isinstance(push_result, dict):
                    if push_result['result'] == 'SUCCESS':
                        self.operator_return['message'] += "To push nodes '%s' successfully.\n" % self.parameters['nodes']
                    else:
                        self.operator_return['message'] += push_result['message']
                        self.operator_return['result'] = 'FAILED'
                else:
                    self.operator_return['message'] += push_result
                    self.operator_return['result'] = 'FAILED'
        else:
            return "ERROR: Your must give only one 'clone_target' node name, Multiple node names are not supported with this parameter!"

        return self.operator_return
