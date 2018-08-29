import json, requests, re, yaml, sys
from .config import *

class APICaller(object):
    def post_caller(self, api_url, post_data=None, isjson=True):
        if isjson:
            try:
                r = requests.post(api_url, json = post_data)
            except:
                return "API ERROR: host not reachable.\n  API URL: %s\n  JSON: %s" % (api_url, str(post_data))
        else:
            try:
                r = requests.post(api_url, data = post_data)
            except:
                return "API ERROR: host not reachable.\n  API URL: %s\n  DATA: %s" % (api_url, str(post_data))

        if r.status_code == 200:
            # To check the data successfully returned by geniusalt_api.
            try:
                return_data = r.json()
            except ValueError:  #This means data returned is a normal string, which cannot be used with r.json().
                return r.text
            else:
                return return_data
        elif r.status_code == 500:
            return "API ERROR: API corrupt."
        else:
            if re.search('^ERROR:', r.text):
                return "API %s\nstatus code: %d" % (r.text, r.status_code)
            else:
                return "API ERROR: %s\nstatus code: %d" % (r.text, r.status_code)

class Handler(APICaller):
    api        = GENIUSALT_API
    auth_token = AUTH_TOKEN
    action    = None
    args      = None

    ### Object attributes parsed from args.
    nodes     = None
    instances = None
    modules   = None
    pillars   = None
    pillar_required   = None
    pillar_optional   = None
    environment       = None
    included_instances = None
    module_belong = None
    show_short = False
    show_instances = False
    push_checkself  = False
    push_only_module = False

    ### action result
    api_return = None
    argParseError = ''

    def getOptionValue(self, opt):
        l = len(self.args)
        i = self.args.index(opt)
        val = None
        if i + 1 < l:
            if not re.search('^\-{1,2}\w+', self.args[i + 1]):
                val = self.args.pop(i + 1)
        self.args.pop(i)
        return val

    def splitNames(self, opt):
        names = []
        opt_value = self.getOptionValue(opt)
        if opt_value:
            for i in opt_value.split(','):
                if i:
                    names.append(i)
        if not names:
            names = None
        return names

    def argParse(self, supported_options):
        args = self.args.copy()
        for i in args:
            if i in supported_options:

                if i == '-p':
                    tmp = self.splitNames(i)
                    pillars  = {}
                    for i in tmp:
                        if '=' in i:
                            p_name = i.split('=')[0]
                            if not p_name:
                                self.argParseError = "ERROR: invalid data for option '-p': %s" % p_name
                                return False
                            p_value = i[i.index('=') + 1:]   ### Means pillar value can be empty string.
                            pillars[p_name] = p_value
                        else:
                            pillars[i] = None
                    if pillars:
                        self.pillars = pillars
                if i == '-mb':
                    self.module_belong = self.getOptionValue(i)
                if i == '-e':
                    self.environment = self.getOptionValue(i)
                if i == '-n':
                    self.nodes = self.splitNames(i)
                if i == '-m':
                    self.modules = self.splitNames(i)
                if i == '-i':
                    self.instances = self.splitNames(i)
                if i == '-ii':
                    self.included_instances = self.splitNames(i)
                if i == '-pr':
                    self.pillar_required = self.splitNames(i)
                if i == '-po':
                    self.pillar_optional = self.splitNames(i)
                if i == '--short':
                    self.show_short = True
                    while '--short' in self.args:
                        self.args.remove('--short')
                if i == '--instance':
                    self.show_instances = True
                    while '--instance' in self.args:
                        self.args.remove('--instance')
                if i == '--checkself':
                    self.push_checkself = True
                    while '--checkself' in self.args:
                        self.args.remove('--checkself')
                if i == '--only-module':
                    self.push_only_module = True
                    while '--only-module' in self.args:
                        self.args.remove('--only-module')

        if self.args:
            self.argParseError = "ERROR: invalid arguments '%s' found for action '%s'"  % (' '.join(self.args), self.action)
            return False

        self.args = args
        return True

    @classmethod
    def error(cls, message, status=1, exit=True):
        print(message)
        if exit:
            sys.exit(status)

    def handleAPIReturn(self):
        if isinstance(self.api_return, str):
            print(self.api_return)
        elif isinstance(self.api_return, dict):
            if self.api_return.get('data'):
                for obj in self.api_return['data']:
                    if obj.get('__showOrder__'):
                        print(obj['name'] + ':' +'\n  ', end='')
                        print(yaml.dump([{i:obj[i]} for i in obj['__showOrder__'] if i != '__showOrder__'], default_flow_style=False).replace('\n','\n  '))
                    else:
                        print(obj['name'])
            if self.api_return.get('message'):
                print(self.api_return['message'])
            if self.api_return.get('pushlog'):
                for node in self.api_return['pushlog']:
                    print("===> Push log for node: %s" % node)
                    for line in self.api_return['pushlog'][node]:
                        print(line)
                    print()

    def call(self, post_data):
        self.post_data.update(post_data)
        self.api_return = self.post_caller(self.api, self.post_data)
        self.handleAPIReturn()
