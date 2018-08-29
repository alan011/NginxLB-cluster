from geniusalt.models import Node, Instance
from geniusalt.config import ENVIRONMENTS
from .common import Operator
import os, re


class NodeOperator(Operator):
    fields_defination = {'name': {'value_type' : 'text',},

                         'environment': {'value_type'   : 'choices',
                                         'value_choices': ENVIRONMENTS},

                         'longTerms':      {'value_type': list,
                                            'item_type': 'choices',
                                            'item_choices':['--short', '--commandline']},

                        }
    def add(self):
        fields_required, fields_optional = ['name'], ['environment']

        ### To validate data in self.parameters.
        validate_result = self.dataValidating(fields_required, fields_optional)
        # print('validate_result: %s' % str(validate_result))
        if not isinstance(validate_result, dict):
            return validate_result

        ### To check object's existence.
        obj = self.getObject(Node, validate_result['name'])
        if obj is not None:
            return "ERROR: Node object has already existed with 'name: %s'." % validate_result['name']

        obj = Node(**validate_result)
        try:
            obj.save()
        except:
            return "ERROR: To add a Node object failed because of some DB related error occurs."

        self.operator_return['message'] = 'To add Node object succeed: %s\n' % validate_result['name']
        return self.operator_return

    def delete(self):
        fields_required, fields_optional = ['name'], []

        ### To validate data in self.parameters.
        validate_result = self.dataValidating(fields_required, fields_optional)
        if not isinstance(validate_result, dict):
            return validate_result

        ### To check object's existence.
        obj = self.getObject(Node, validate_result['name'])
        if obj is None:
            return "ERROR: Node object not exist with 'name: %s'." % validate_result['name']

        ### To delete object.
        try:
            obj.delete()
        except:
            return "ERROR: To delete Node object failed because of some DB related error occurs."

        self.operator_return['message'] = 'To delete Node object succeed: %s\n' % validate_result['name']
        return self.operator_return

    def environmentSet(self):
        fields_required, fields_optional = ['name'], []

        environment = ''
        if not ('environment' in self.parameters and self.parameters['environment'] == environment):
            fields_required.append('environment')

        ### To validate data in self.parameters.
        validate_result = self.dataValidating(fields_required, fields_optional)
        if not isinstance(validate_result, dict):
            return validate_result
        if validate_result.get('environment'):
            environment = validate_result['environment']

        ### To check object's existence.
        obj = self.getObject(Node, validate_result['name'])
        if obj is None:
            return "ERROR: Node object not exist with 'name: %s'." % validate_result['name']

        ### To set environment of Node obj.
        obj.environment = environment
        try:
            obj.save()
        except:
            "ERROR: To set environment for Node '%s' failed because of some DB related error occurs." % validate_result['name']

        self.operator_return['message'] = "To set Node '%s' to environment '%s' succeed.\n" % (obj.name, environment)
        return self.operator_return

    def lock(self):
        fields_required, fields_optional = ['name'], []

        ### To validate data in self.parameters.
        validate_result = self.dataValidating(fields_required, fields_optional)
        if not isinstance(validate_result, dict):
            return validate_result

        ### To check object's existence.
        obj = self.getObject(Node, validate_result['name'])
        if obj is None:
            return "ERROR: Node object not exist with 'name: %s'." % validate_result['name']

        ### To make lock.
        obj.is_lock = 1
        try:
            obj.save()
        except:
            return "ERROR: To lock Node object failed because of some DB related error occurs."

        self.operator_return['message'] = 'To lock Node object succeed: %s\n' % validate_result['name']
        return self.operator_return

    def unlock(self):
        fields_required, fields_optional = ['name'], []

        ### To validate data in self.parameters.
        validate_result = self.dataValidating(fields_required, fields_optional)
        if not isinstance(validate_result, dict):
            return validate_result

        ### To check object's existence.
        obj = self.getObject(Node, validate_result['name'])
        if obj is None:
            return "ERROR: Node object not exist with 'name: %s'." % validate_result['name']

        ### To make unlock.
        obj.is_lock = 0
        try:
            obj.save()
        except:
            return "ERROR: To unlock Node object failed because of some DB related error occurs."

        self.operator_return['message'] = 'To unlock Node object succeed: %s\n' % validate_result['name']
        return self.operator_return

    def show(self):
        fields_required, fields_optional = [], ['name', 'longTerms']

        ### To validate data in self.parameters.
        validate_result = self.dataValidating(fields_required, fields_optional)
        if not isinstance(validate_result, dict):
            return validate_result

        ### To make query.
        if 'name' in self.parameters:
            ### To check object's existence.
            queryset = Node.objects.filter(name = validate_result['name'])
            if not queryset.exists():
                return "ERROR: Node object not exist with 'name: %s'." % validate_result['name']
        else:
            queryset = Node.objects.all()

        ### To make return data
        data = []
        for obj in queryset.order_by('id'):
            if 'longTerms' in self.parameters and '--short' in validate_result['longTerms']:
                attrs = {'name':obj.name}
            else:
                attrs = {'name': obj.name,
                        'is_lock': obj.is_lock,
                        'environment': obj.environment,
                        'pillar':obj.pillar(),
                        }
                if 'longTerms' in self.parameters and '--commandline' in validate_result['longTerms']:
                    attrs['__showOrder__'] = ['name', 'is_lock', 'environment', 'pillar']

            data.append(attrs)

        self.operator_return['data'] = data
        return self.operator_return

    def scan(self):
        if not os.path.isfile('/usr/bin/salt-key'):
            return "ERROR: Bin file ''/usr/bin/salt-key' is not found. This may because salt-master is not installed on this host properly."

        nodes = []
        fa = os.popen('/usr/bin/salt-key -l acc')
        for line in fa:
            line_content = line.strip()
            if line_content and not re.search('^Accepted Keys', line_content):
                nodes.append(line_content)
        fu = os.popen('/usr/bin/salt-key -l un')
        for line in fu:
            line_content = line.strip()
            if line_content and not re.search('^Unaccepted Keys', line_content):
                nodes.append(line_content)
                os.system('/usr/bin/salt-key -a %s' % line_content)

        for node in nodes:
            obj = self.getObject(Node, node)
            if obj:
                self.operator_return['message'] += "Duplicated node '%s', ignored.\n" % node
            else:
                new_obj = Node(name=node)
                try:
                    new_obj.save()
                except:
                    return "ERROR: Fail to save node object, DB related error ocurred."
                self.operator_return['message'] += "Add new node: %s\n" % node
        return self.operator_return
