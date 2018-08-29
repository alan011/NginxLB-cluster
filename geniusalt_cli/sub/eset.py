from .common import Handler

class Eset(Handler):
    def eset(self):
        supported_options = ['-n' , '-e']
        if not self.argParse(supported_options):
            self.error(self.argParseError)
        if not self.nodes or not self.environment:
            self.error("ERROR: action 'eset' can only be used to set environment of node objects. Option '-n' and '-e' must be specified.")

        for name in self.nodes:
            post_data = {'object':'node', 'name':name, 'environment':self.environment}
            self.call(post_data)
