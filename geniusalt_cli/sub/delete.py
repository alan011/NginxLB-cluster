from .common import Handler

class Delete(Handler):
    def delete(self):
        supported_options = ['-n', '-m', '-i']

        if not self.argParse(supported_options):
            self.error(self.argParseError)

        if self.nodes:
            for name in self.nodes:
                post_data = {'object':'node', 'name':name}
                self.call(post_data)

        if self.modules:
            for name in self.modules:
                answer = input("Warning: all instances belong to module '%s' will be deleted cascadedly.\nDo you really want to do that? [Y/N]" % name)
                if answer == 'Y':
                    post_data = {'object':'module', 'name':name}
                    self.call(post_data)
                else:
                    print("OK, To delete module '%s' aborted." % name)

        if self.instances:
            for name in self.instances:
                post_data = {'object':'instance', 'name':name}
                self.call(post_data)
