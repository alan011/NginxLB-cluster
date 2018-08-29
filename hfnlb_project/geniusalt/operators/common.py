import re

class Operator(object):
    fields_defination = {}
    def __init__(self, parameters):
        self.parameters = parameters
        self.operator_return = {'result':'SUCCESS', 'message':''}

    def getObject(self, model, object_name, **kwargs):
        data_filter = {'name':object_name}
        data_filter.update(kwargs)
        queryset = model.objects.filter(**data_filter)
        if queryset.exists():
            return queryset.get(**data_filter)
        return None

    def dataValidating(self, fields_required, fields_optional):
        """
        Subclass need to define attribute 'fields_defination'.
        """
        for field in fields_required:
            if not self.parameters.get(field):  ### Means must be provided and its value should not be empty.
                return "ERROR: Field '%s' is required." % field

        legal_data = {}
        for field in fields_required + fields_optional:
            has_collected = 0
            if field in self.parameters:
                if self.fields_defination[field]['value_type'] == str:
                    if not isinstance(self.parameters[field], str):
                        return "ERROR: Value of field '%s' must be a string." % field
                    if not re.search(self.fields_defination[field]['value_regex'], self.parameters[field]):
                        return "ERROR: Value of field '%s' contains illegal characters." % field

                if self.fields_defination[field]['value_type'] == 'choices' and self.parameters[field] not in self.fields_defination[field]['value_choices']:
                    return "ERROR: Illegal value '%s' found for choices field '%s'." % (self.parameters[field],field)

                if self.fields_defination[field]['value_type'] == list:
                    if not isinstance(self.parameters[field], list):
                        return "ERROR: Value of field '%s' must be a JSON list." % field
                    if self.fields_defination[field]['item_type'] == str:
                        for item in self.parameters[field]:
                            if not isinstance(item, str):
                                return "ERROR: Item '%s' of list field '%s' must be a string." % (item, field)
                            if not re.search(self.fields_defination[field]['item_regex'], item):
                                return "ERROR: Item '%s' of list field '%s' contains illegal characters." % (item,field)
                    if self.fields_defination[field]['item_type'] == 'choices':
                        for item in self.parameters[field]:
                            if item not in self.fields_defination[field]['item_choices']:
                                return "ERROR: Illegal item '%s' found for item-choice-type list field '%s' ." % (item,field)

                    if self.fields_defination[field]['item_type'] == 'object_name_list':
                        model = self.fields_defination[field]['item_model']
                        object_list = []
                        for n in self.parameters[field]:
                            obj = self.getObject(model, n)
                            if obj is None:
                                return "ERROR: Object not found for name '%s' in field '%s'." % (n, field)
                            object_list.append(obj)
                        legal_data[field] = object_list
                        has_collected = 1

                if self.fields_defination[field]['value_type'] == 'object_name':
                    model = self.fields_defination[field]['object_model']
                    obj = self.getObject(model, self.parameters[field])
                    if obj is None:
                        return "ERROR: Object not found for field '%s'." % field
                    legal_data[field] = obj
                    has_collected = 1

                if self.fields_defination[field]['value_type'] == dict:
                    if not isinstance(self.parameters[field], dict):
                        return "ERROR: Value of field '%s' must be a JSON dict." % field
                    if self.fields_defination[field]['key_type'] == str:
                        for key in self.parameters[field]:
                            if not isinstance(key, str):
                                return "ERROR: Key '%s' of dict field '%s' must be a string." % (key, field)
                            if not re.search(self.fields_defination[field]['key_regex'], key):
                                return "ERROR: Key '%s' of dict field '%s' contains illegal characters." % (item,field)

                if self.fields_defination[field]['value_type'] == 'text':
                    legal_data[field] = str(self.parameters[field])
                    has_collected = 1

                if has_collected == 0:
                    legal_data[field] = self.parameters[field]
        return legal_data
