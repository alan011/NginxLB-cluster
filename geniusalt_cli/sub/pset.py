from .common import Handler

class Pset(Handler):
    def pset(self):
        supported_options = ['-i' , '-p', '-e']
        if not self.argParse(supported_options):
            self.error(self.argParseError)
        if not self.instances or not self.pillars:
            self.error("ERROR: action 'pset' can only be used to set pillars of instance objects. Option '-i' and '-p' must be specified, option '-e' can be optionally used to set environment related pillars.")

        for name in self.instances:
            post_data = {'object':'instance', 'name':name, 'pillar':self.pillars}
            if self.environment:
                post_data['environment'] = self.environment
            self.call(post_data)
