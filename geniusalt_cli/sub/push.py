from .common import Handler

class Push(Handler):
    def push(self):
        supported_options = ['-n' , '-m', '-i', '--checkself', '--only-module']
        if not self.argParse(supported_options):
            self.error(self.argParseError)
        if not self.nodes:
            self.error("ERROR: action 'push' requires node objects specified.")

        post_data = {'object':'push', 'nodes':self.nodes}
        if self.modules:
            post_data['bind_modules'] = self.modules
        if self.instances:
            post_data['bind_instances'] = self.instances
        if self.push_checkself:
            post_data['longTerms'] = ['--checkself']
        if self.push_only_module:
            if post_data.get('longTerms'):
                post_Data['longTerms'].append('--only-module')
            else:
                post_data['longTerms'] = ['--only-module']
        self.call(post_data)
