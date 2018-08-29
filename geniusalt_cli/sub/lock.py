from .common import Handler

class Lock(Handler):
    def lock_common_method(self):
        supported_options = ['-n' , '-m', '-i']
        if not self.argParse(supported_options):
            self.error(self.argParseError)
        if not (self.instances or self.nodes or self.modules):
            self.error("ERROR: action '%s' requires at least one of option '-i', '-m' or '-n'." % self.action)

        if self.nodes:
            for name in self.nodes:
                post_data = {'object':'node', 'name':name}
                self.call(post_data)
        if self.instances:
            for name in self.instances:
                post_data = {'object':'instance', 'name':name}
                self.call(post_data)
        if self.modules:
            for name in self.modules:
                post_data = {'object':'module', 'name':name}
                self.call(post_data)

    def lock(self):
        self.lock_common_method()

    def unlock(self):
        self.lock_common_method()
