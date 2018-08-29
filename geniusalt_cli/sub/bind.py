from .common import Handler

class Bind(Handler):
    def bind_common(self):
        supported_options = ['-n', '-i', '-m']
        if not self.argParse(supported_options):
            self.error(self.argParseError)
        if not self.nodes or not (self.instances or self.modules):
            self.error("ERROR: action '%s' is used to %s instances or modules to node objects. Option '-n' must be specified. At least one of Option '-i' or '-m' must also be specified." % (self.action, self.action))

        post_data = {'object':'relation', 'nodes': self.nodes}
        if self.modules:
            post_data['bind_modules'] = self.modules
        if self.instances:
            post_data['bind_instances'] = self.instances
        self.call(post_data)
    def bind(self):
        self.bind_common()
    def unbind(self):
        self.bind_common()
