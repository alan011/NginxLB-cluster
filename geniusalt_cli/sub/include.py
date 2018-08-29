from .common import Handler

class Include(Handler):
    def include_common(self):
        supported_options = ['-i' , '-ii']
        if not self.argParse(supported_options):
            self.error(self.argParseError)
        if not self.instances or not self.included_instances:
            self.error("ERROR: action '%s' is used for an instances to %s other instances. Option '-i' and '-ii' must be specified." % (self.action, self.action))
        post_data = {'object':'relation', 'instances': self.instances, 'included_instances':self.included_instances}
        self.call(post_data)
    def include(self):
        self.include_common()
    def exclude(self):
        self.include_common()
