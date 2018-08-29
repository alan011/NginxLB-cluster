from .common import Handler

class Pdel(Handler):
    def pdel(self):
        supported_options = ['-i' , '-p', '-e']
        if not self.argParse(supported_options):
            self.error(self.argParseError)
        if not self.instances or not self.pillars:
            self.error("ERROR: action 'pdel' can only be used to delete pillars of instance objects. Option '-i' and '-p' must be specified, option '-e' can be optionally used to delete environment related pillars.")

        for name in self.instances:
            for pillar_name in self.pillars:
                post_data = {'object':'instance', 'name':name, 'pillar_name':pillar_name}
                if self.environment:
                    post_data['environment'] = self.environment
                self.call(post_data)
