from geniusalt.models import Module
from geniusalt.config import SALT_FILE_ROOT
from .common import Operator
import re, os, json

class ModuleOperator(Operator):
    fields_defination = {'name': {'value_type' :str,
                                  'value_regex':'[a-zA-Z]+[0-9a-zA-Z_\-]*[a-zA-Z0-9]+$'},
                         'pillar_required':{'value_type': list,
                                            'item_type': str,
                                            'item_regex':'^[a-zA-Z]+[0-9a-zA-Z_\-]*$'},
                         'pillar_optional':{'value_type': list,
                                            'item_type': str,
                                            'item_regex':'^[a-zA-Z]+[0-9a-zA-Z_\-]*$'},
                         'longTerms':      {'value_type': list,
                                            'item_type': 'choices',
                                            'item_choices':['--short','--instance', '--commandline']},
                        }

    def add(self):
        fields_required, fields_optional = ['name'],['pillar_required', 'pillar_optional']

        ### To validate data in self.parameters.
        validate_result = self.dataValidating(fields_required, fields_optional)
        if not isinstance(validate_result, dict):
            return validate_result

        ### To check object's existence.
        obj = self.getObject(Module, validate_result['name'])
        if obj is not None:
            return "ERROR: Module object has already existed with 'name: %s'." % self.parameters['name']

        obj = Module(**validate_result)
        try:
            obj.save()
        except:
            return "ERROR: To add a Module object failed because of some DB related error occurs."

        self.operator_return['message'] = 'To add Module object succeed: %s\n' % validate_result['name']
        return self.operator_return

    def delete(self):
        fields_required, fields_optional = ['name'], []

        ### To validate data in self.parameters.
        validate_result = self.dataValidating(fields_required, fields_optional)
        if not isinstance(validate_result, dict):
            return validate_result

        ### To check object's existence.
        obj = self.getObject(Module, validate_result['name'])
        if obj is None:
            return "ERROR: Module object not exist with 'name: %s'." % validate_result['name']

        ### To delete object.
        try:
            obj.delete()
        except:
            return "ERROR: To delete Module object failed because of some DB related error occurs."

        self.operator_return['message'] = 'To delete Module object succeed: %s\n' % validate_result['name']
        return self.operator_return

    def lock(self):
        fields_required, fields_optional = ['name'], []

        ### To validate data in self.parameters.
        validate_result = self.dataValidating(fields_required, fields_optional)
        if not isinstance(validate_result, dict):
            return validate_result

        ### To check object's existence.
        obj = self.getObject(Module, validate_result['name'])
        if obj is None:
            return "ERROR: Module object not exist with 'name: %s'." % validate_result['name']

        ### To make lock.
        obj.lock_count += 1
        try:
            obj.save()
        except:
            return "ERROR: To lock Module object failed because of some DB related error occurs."

        self.operator_return['message'] = 'To lock Module object succeed: %s\n' % validate_result['name']
        return self.operator_return

    def unlock(self):
        fields_required, fields_optional = ['name'], []

        ### To validate data in self.parameters.
        validate_result = self.dataValidating(fields_required, fields_optional)
        if not isinstance(validate_result, dict):
            return validate_result

        ### To check object's existence.
        obj = self.getObject(Module, validate_result['name'])
        if obj is None:
            return "ERROR: Module object not exist with 'name: %s'." % validate_result['name']

        ### To make unlock.
        if obj.lock_count > 0:
            obj.lock_count -= 1
        try:
            obj.save()
        except:
            return "ERROR: To unlock Module object failed because of some DB related error occurs."

        self.operator_return['message'] = 'To unlock Module object succeed: %s\n' % validate_result['name']
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
            queryset = Module.objects.filter(name = validate_result['name'])
            if not queryset.exists():
                return "ERROR: Module object not exist with 'name: %s'." % validate_result['name']
        else:
            queryset = Module.objects.all()

        ### To make return data
        data = []
        for obj in queryset.order_by('id'):
            if 'longTerms' in self.parameters and '--short' in validate_result['longTerms']:
                attrs = {'name':obj.name}
            else:
                attrs = {'name': obj.name,
                        'lock_count': obj.lock_count,
                        'pillar_required': obj.pillar_required,
                        'pillar_optional': obj.pillar_optional,
                        }
                if 'longTerms' in self.parameters and '--commandline' in validate_result['longTerms']:
                    attrs['__showOrder__'] = ['name', 'lock_count', 'pillar_required', 'pillar_optional']

            if 'longTerms' in self.parameters and '--instance' in validate_result['longTerms']:
                instance_queryset = obj.instances.all()
                attrs['instances'] = [i_obj.name for i_obj in instance_queryset]
                if attrs.get('__showOrder__'):
                    attrs['__showOrder__'].append('instances')

            data.append(attrs)

        self.operator_return['data'] = data
        return self.operator_return

    def showBind(self):
        fields_required, fields_optional = ['name'], ['longTerms']

        ### To validate data in self.parameters.
        validate_result = self.dataValidating(fields_required, fields_optional)
        if not isinstance(validate_result, dict):
            return validate_result

        ### To check object's existence.
        obj = self.getObject(Module, validate_result['name'])
        if obj is None:
            return "ERROR: Module object not exist with 'name: %s'." % validate_result['name']

        ### To get Node data.
        node_data = []
        for n_obj in obj.node_set.all():
            if 'longTerms' in self.parameters and '--short' in validate_result['longTerms']:
                attrs = {'name':n_obj.name}
            else:
                attrs = {'name': n_obj.name,
                        'is_lock': n_obj.is_lock,
                        'environment': n_obj.environment,
                        'pillar':n_obj.pillar(),
                        }
                if 'longTerms' in self.parameters and '--commandline' in validate_result['longTerms']:
                    attrs['__showOrder__'] = ['name', 'is_lock', 'environment', 'pillar']

            node_data.append(attrs)

        self.operator_return['data'] = node_data
        return self.operator_return

    def scan(self):
        mod_scan = []
        for m in os.listdir(SALT_FILE_ROOT):
            pillar_required = []
            pillar_optional = []
            is_module = False
            if os.path.isdir(os.path.join(SALT_FILE_ROOT,m)):
                module_file = os.path.join(SALT_FILE_ROOT,m,'init.sls')
                config_file = os.path.join(SALT_FILE_ROOT,m,'pillar.json')
                if os.path.isfile(module_file):
                    is_module = True
                    if os.path.isfile(config_file):
                        try:
                            pillar_config = json.loads(open(config_file).read())
                        except:
                            return "ERROR: Invalid 'pillar.json' file, content is not a valid json string."

                        if not isinstance(pillar_config, dict):
                            return "ERROR: Invalid 'pillar.json' file, content is not a valid json dict."

                        if pillar_config.get('pillar_required') and isinstance(pillar_config['pillar_required'], list):
                            for i in pillar_config['pillar_required']:
                                if not isinstance(i, str):
                                    return "ERROR: Invalid 'pillar.json' file, pillar variable name must be a string."
                                if not re.search(self.fields_defination['pillar_required']['item_regex'], i):
                                    return "ERROR: Invalid 'pillar.json' file, invalid pillar variable name found: %s." % i
                                pillar_required.append(i)
                        if pillar_config.get('pillar_optional') and isinstance(pillar_config['pillar_optional'], list):
                            for i in pillar_config['pillar_optional']:
                                if not isinstance(i, str):
                                    return "ERROR: Invalid 'pillar.json' file, pillar variable name must be a string."
                                if not re.search(self.fields_defination['pillar_optional']['item_regex'], i):
                                    return "ERROR: Invalid 'pillar.json' file, invalid pillar variable name found: '%s'." % i
                                pillar_optional.append(i)
                        for k in pillar_config:
                            if k not in ['pillar_required', 'pillar_optional']:
                                self.operator_return['message'] += "WARNING: module '%s' ingored illegal config option: '%s'\n" % (m,k)
            if is_module:
                pillar_required.sort()
                pillar_optional.sort()
                if re.search(self.fields_defination['name']['value_regex'], m):
                    mod_scan.append({'name':m,'pillar_required':pillar_required,'pillar_optional':pillar_optional})
                else:
                    self.operator_return['message'] += "WARNING: Illegal module name found: '%s'.\n" % m

        for m_dict in mod_scan:
            m_queryset = Module.objects.filter(name=m_dict['name'])
            if m_queryset.exists():
                m_obj = m_queryset.get(name=m_dict['name'])
                p_r = m_obj.pillar_required
                p_o = m_obj.pillar_optional
                p_r.sort()
                p_o.sort()
                if p_r != m_dict['pillar_required'] or p_o != m_dict['pillar_optional']:
                    m_obj.pillar_required = m_dict['pillar_required']
                    m_obj.pillar_optional = m_dict['pillar_optional']
                    m_obj.save()
                    self.operator_return['message'] += "To update module '%s' successfully.\n" % m_dict['name']
                else:
                    self.operator_return['message'] += "Ignore module '%s', nothing changed.\n" % m_dict['name']
            else:

                m_obj = Module(**m_dict)
                m_obj.save()
                self.operator_return['message'] += "To add new module '%s' successfully.\n" % m_dict['name']
        return self.operator_return
