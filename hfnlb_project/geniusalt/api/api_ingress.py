from django.views.generic import View
from django.http          import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators      import method_decorator


import json

from geniusalt.operators import ModuleOperator, InstanceOperator, NodeOperator, RelationOperator, PushOperator
from .auth import authenticate

@method_decorator(csrf_exempt, name='dispatch')
class GeniusaltIngress(View):
    type_words = {
        ModuleOperator:   ['module', '-m', 'mod'],
        InstanceOperator: ['instance', '-i', 'inst'],
        NodeOperator:     ['node', '-n'],
        RelationOperator: ['relation'],
        PushOperator:     ['push'],
        }
    actions = {
        'scan':         {'operators':[ModuleOperator, NodeOperator,],'alias':[]},
        'add':          {'operators':[ModuleOperator, InstanceOperator, NodeOperator,],'alias':[]},
        'delete':       {'operators':[ModuleOperator, InstanceOperator, NodeOperator,],'alias':['del']},
        'show':         {'operators':[ModuleOperator, InstanceOperator, NodeOperator,],'alias':[]},
        'pillarSet':    {'operators':[InstanceOperator,],'alias':['pset']},
        'pillarDel':    {'operators':[InstanceOperator,],'alias':['pdel']},
        'environmentSet':{'operators':[NodeOperator,],'alias':['eset', 'envSet']},
        'lock':         {'operators':[ModuleOperator, InstanceOperator, NodeOperator,],'alias':[]},
        'unlock':       {'operators':[ModuleOperator, InstanceOperator, NodeOperator,],'alias':[]},
        'showBind':     {'operators':[ModuleOperator,InstanceOperator],'alias':['showb']},
        'include':      {'operators':[RelationOperator,],'alias':[]},
        'exclude':      {'operators':[RelationOperator,],'alias':[]},
        'hasInclude':   {'operators':[RelationOperator,],'alias':[]},
        'bind':         {'operators':[RelationOperator,],'alias':[]},
        'unbind':       {'operators':[RelationOperator,],'alias':[]},
        'clone':        {'operators':[RelationOperator,],'alias':[]},
        'push':         {'operators':[PushOperator,],'alias':[]},
        }


    def json_load(self, decode_type='utf-8'):
        try:
            post_data   = json.loads(self.request.body.decode(decode_type))
        except:
            return HttpResponse("ERROR: To load json data failed.", status=400)
        # print('POST DATA: %s' % str(post_data))
        if isinstance(post_data, dict):
            return post_data
        else:
            return HttpResponse("ERROR: Post data illegal.", status=400)

    def get(self, request, *args, **kwargs):
        return HttpResponse('ERROR: Get method is not allowed.', status=400)

    def post(self, request, *args, **kwargs):
        ### To check post data in JSON.
        post_data = self.json_load()
        if isinstance(post_data, HttpResponse):
            return post_data

        ### To authenticate request.
        if not authenticate(post_data):
            return HttpResponse("ERROR: Authentication failed.", status = 403)

        ### To dispatch operating methods by 'action' and 'object'.
        action = post_data.get('action')
        if not action:
            return HttpResponse("ERROR: 'action' field is required.", status=400)
        object_type = post_data.get('object')
        if not object_type:
            return HttpResponse("ERROR: 'object' field is required.", status=400)

        operator = None
        for method in self.actions:
            if action == method or action in self.actions[method]['alias']:  ### To filter out invalid actions
                operator_method = method
                for operator_class in self.type_words:
                    if object_type in self.type_words[operator_class]: ### To filter out invalid object_types
                        operator = operator_class(parameters = post_data)
        if operator is None:
            return HttpResponse("ERROR: 'action: %s' or 'object: %s' your provided is not supported." % (action, object_type), status=400)

        ### To do the real work.
        operator_return = getattr(operator, operator_method)()
        if isinstance(operator_return, dict):
            return HttpResponse(json.dumps(operator_return), content_type='application/json')
        else:
            return HttpResponse(str(operator_return), status=400)
