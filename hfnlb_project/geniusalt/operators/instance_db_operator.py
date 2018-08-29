from geniusalt.models import Module, Instance, Node, Pillar, IncludeRelationship
from geniusalt.config import ENVIRONMENTS
from .common import Operator

class InstanceOperator(Operator):
    fields_defination = {'name': {'value_type' : str,
                                  'value_regex': '^[a-zA-Z]+[0-9a-zA-Z_\-\.]*[a-zA-Z0-9]+$'},

                         'environment': {'value_type'   : 'choices',
                                         'value_choices': ENVIRONMENTS},

                         'pillar':{'value_type': dict,
                                    'key_type':  str,
                                    'key_regex':'^[a-zA-Z]+[0-9a-zA-Z_\-]*$',
                                    'val_type': 'text'
                                        ### Difference between 'text' and str is, str requires it must be a TYPE str;
                                        ### 'text' has no such requirements, if it's not a str, auto-transifer it to be a str.
                                   },

                         'pillar_name':{'value_type': str,
                                        'value_regex': '^[a-zA-Z]+[0-9a-zA-Z_\-]*$'},

                         'module_belong': {'value_type': 'object_name',
                                           'object_model': Module,
                                           },

                         'longTerms':      {'value_type': list,
                                            'item_type': 'choices',
                                            'item_choices':['--short','--commandline']},

                        }
    def checkPillarRequired(self, module_obj, pillar):
        for p in module_obj.pillar_required:
            if p not in pillar:
                return "ERROR: pillar '%s' is required for module '%s'." % (p, module_obj.name)
        for p in pillar:
            if p not in module_obj.pillar_required + module_obj.pillar_optional:
                pillar.pop(p)
        return 'SUCCESS'

    def fillPillar(self, instance_obj, pillar, environment):
        warning_message = ''
        for p in pillar:
            attrs = {'pillar_name':p,
                    'pillar_value': str(pillar[p]),
                    'instance_belong': instance_obj,
                    'environment': environment,
                    }
            p_obj = Pillar(**attrs)
            try:
                p_obj.save()
            except:
                warning_message += "WARNING: To fill pillar '%s' for instance '%s' failed. Instance may not work as you expected. Please remember to reset this pillar appropriately later!\n" % (p, instance_obj.name)
        if warning_message:
            return warning_message
        return 'SUCCESS'

    def add(self):
        fields_required, fields_optional = ['name', 'module_belong'], ['pillar', 'environment']

        if 'environment' in self.parameters and self.parameters['environment'] == '':
            self.parameters.pop('environment')
        ### To validate data in self.parameters.
        validate_result = self.dataValidating(fields_required, fields_optional)
        if not isinstance(validate_result, dict):
            return validate_result

        ### To check object's existence.
        obj = self.getObject(Instance, validate_result['name'])
        if obj is not None:
            return "ERROR: Instance object has already existed with 'name: %s'." % self.parameters['name']

        ### To remove attributes for Pillar, and check it.
        pillar = {}
        environment = ''
        if 'pillar' in validate_result:
            pillar = validate_result.pop('pillar')
        check_result = self.checkPillarRequired(validate_result['module_belong'],pillar)
        if check_result != 'SUCCESS':
            return check_result

        if 'environment' in validate_result:
            environment = validate_result.pop('environment')

        obj = Instance(**validate_result)
        try:
            obj.save()
        except:
            return "ERROR: To add a Instance object failed because of some DB related error occurs."
        self.operator_return['message'] = "To add Instance object succeeded: %s\n" % validate_result['name']

        ### To fill pillar for this instance.
        fill_result = self.fillPillar(obj, pillar, environment)
        if fill_result != 'SUCCESS':
            self.operator_return['message'] += fill_result

        return self.operator_return

    def delete(self):
        fields_required, fields_optional = ['name'], []

        ### To validate data in self.parameters.
        validate_result = self.dataValidating(fields_required, fields_optional)
        if not isinstance(validate_result, dict):
            return validate_result

        ### To check object's existence.
        obj = self.getObject(Instance, validate_result['name'])
        if obj is None:
            return "ERROR: Instance object not exist with 'name: %s'." % validate_result['name']

        ### To delete object.
        try:
            obj.delete()
        except:
            return "ERROR: To delete Instance object failed because of some DB related error occurs."

        self.operator_return['message'] = 'To delete Instance object succeeded: %s' % validate_result['name']
        return self.operator_return

    def pillarSet(self):
        fields_required, fields_optional = ['name', 'pillar'], ['environment']
        self.operator_return['message'] = ''

        if 'environment' in self.parameters and self.parameters['environment'] == '':
            self.parameters.pop('environment')
        ### To validate data in self.parameters.
        validate_result = self.dataValidating(fields_required, fields_optional)
        if not isinstance(validate_result, dict):
            return validate_result

        ### To check object's existence.
        obj = self.getObject(Instance, validate_result['name'])
        if obj is None:
            return "ERROR: Instance object not exist with 'name: %s'." % validate_result['name']

        legal_pillars = obj.module_belong.pillar_required + obj.module_belong.pillar_optional
        environment = ''
        if validate_result.get('environment'):
            environment = validate_result['environment']

        pillar_queryset = obj.pillars.filter(environment = environment)
        for p_obj in pillar_queryset: ### To make sure pillar_name is unique for one instance, in same environment.
            if p_obj.pillar_name in validate_result['pillar']:
                p_obj.pillar_value = validate_result['pillar'].pop(p_obj.pillar_name)
                p_obj.save()

        for p in validate_result['pillar']:
            if p in legal_pillars:
                fill_result = self.fillPillar(obj, validate_result['pillar'], environment)
                if fill_result != 'SUCCESS':
                    self.operator_return['message'] += fill_result

        self.operator_return['message'] += "To set pillar for instance '%s' succeeded.\n" % obj.name
        return self.operator_return

    def pillarDel(self):
        fields_required, fields_optional = ['name', 'pillar_name'], ['environment']

        ### To validate data in self.parameters.
        validate_result = self.dataValidating(fields_required, fields_optional)
        if not isinstance(validate_result, dict):
            return validate_result

        ### To check object's existence.
        obj = self.getObject(Instance, validate_result['name'])
        if obj is None:
            return "ERROR: Instance object not exist with 'name: %s'." % validate_result['name']

        environment = ''
        if validate_result.get('environment'):
            environment = validate_result['environment']

        pillar_queryset = obj.pillars.filter(environment = environment, pillar_name=validate_result['pillar_name'])
        if not pillar_queryset.exists():
            return "ERROR: Instance '%s' in environment '%s' has no such a pillar '%s'." % (obj.name, environment, validate_result['pillar_name'])

        p_obj = pillar_queryset.get(environment = environment, pillar_name=validate_result['pillar_name'])
        for p_obj in pillar_queryset:
            p_obj.delete()

        self.operator_return['message'] = "To delete pillar '%s' of instance '%s' succeeded in environment '%s'.\n" % (validate_result['pillar_name'], obj.name, environment)
        return self.operator_return

    def lock(self):
        fields_required, fields_optional = ['name'], []

        ### To validate data in self.parameters.
        validate_result = self.dataValidating(fields_required, fields_optional)
        if not isinstance(validate_result, dict):
            return validate_result

        ### To check object's existence.
        obj = self.getObject(Instance, validate_result['name'])
        if obj is None:
            return "ERROR: Instance object not exist with 'name: %s'." % validate_result['name']

        ### To make lock.
        obj.is_lock = 1
        try:
            obj.save()
        except:
            return "ERROR: To lock Instance object failed because of some DB related error occurs."

        self.operator_return['message'] = 'To lock Instance object succeeded: %s\n' % validate_result['name']
        return self.operator_return

    def unlock(self):
        fields_required, fields_optional = ['name'], []

        ### To validate data in self.parameters.
        validate_result = self.dataValidating(fields_required, fields_optional)
        if not isinstance(validate_result, dict):
            return validate_result

        ### To check object's existence.
        obj = self.getObject(Instance, validate_result['name'])
        if obj is None:
            return "ERROR: Instance object not exist with 'name: %s'." % validate_result['name']

        ### To make unlock.
        obj.is_lock = 0
        try:
            obj.save()
        except:
            return "ERROR: To unlock Instance object failed because of some DB related error occurs."

        self.operator_return['message'] = 'To unlock Instance object succeeded: %s\n' % validate_result['name']
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
            queryset = Instance.objects.filter(name = validate_result['name'])
            if not queryset.exists():
                return "ERROR: Instance object not exist with 'name: %s'." % validate_result['name']
        else:
            queryset = Instance.objects.all()

        ### To make return data
        data = []
        for obj in queryset.order_by('id'):
            if 'longTerms' in self.parameters and '--short' in validate_result['longTerms']:
                attrs = {'name':obj.name}
            else:
                attrs = {'name': obj.name,
                        'module_belong':obj.module_belong.name,
                        'is_lock': obj.is_lock,
                        'pillar': {p.pillar_name: p.pillar_value for p in obj.pillars.filter(environment='')},
                        'included_instances':[],
                        }
                for env in ENVIRONMENTS:
                    env_pillar = {p.pillar_name: p.pillar_value for p in obj.pillars.filter(environment=env)}
                    if env_pillar:
                        attrs['pillar/' + env] = env_pillar
                r_queryset =IncludeRelationship.objects.filter(r_instance=obj)
                if r_queryset.exists():
                    r_obj = r_queryset.get(r_instance=obj)
                    attrs['included_instances'] = [ i.name for i in r_obj.r_included.all()]

                if 'longTerms' in self.parameters and '--commandline' in validate_result['longTerms']:
                    attrs['__showOrder__'] = ['name', 'module_belong', 'is_lock', 'pillar']
                    for env in ENVIRONMENTS:
                        if 'pillar/' + env in attrs:
                            attrs['__showOrder__'].append('pillar/' + env)
                    attrs['__showOrder__'].append('included_instances')

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
        obj = self.getObject(Instance, validate_result['name'])
        if obj is None:
            return "ERROR: Instance object not exist with 'name: %s'." % validate_result['name']

        ### To get Node data.
        data = []
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
            data.append(attrs)

        self.operator_return['data'] = data
        return self.operator_return
