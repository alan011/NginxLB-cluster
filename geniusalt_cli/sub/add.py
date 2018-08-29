from .common import Handler

class Add(Handler):
    def add(self):
        supported_options = ['-n','-e','-m','-pr', '-po', '-i','-p','-mb']
        if not self.argParse(supported_options):
            self.error(self.argParseError)
        if not (self.nodes or self.modules or self.instances):
            self.error("ERROR: Add command requires an object name, which can be specified with option '-n, -m or -i'.")
        if (self.nodes and self.modules) or (self.nodes and self.instances) or (self.modules and self.instances):
            self.error("ERROR: Only one option '-n, -m or -i' can be specified.")

        if self.nodes:
            for name in self.nodes:
                post_data = {'object':'node', 'name':name}
                if self.environment:
                    post_data['environment'] = self.environment
                self.call(post_data)

        if self.modules:
            for name in self.modules:
                post_data = {'object':'module', 'name':name}
                if self.pillar_required:
                    post_data['pillar_required'] = self.pillar_required
                if self.pillar_optional:
                    post_data['pillar_optional'] = self.pillar_optional
                self.call(post_data)

        if self.instances:
            if not self.module_belong:
                self.error("ERROR: instance must belong to a module, use '-mb' to specify it.")
            for name in self.instances:
                post_data = {'object':'instance', 'name':name, 'module_belong': self.module_belong}
                if self.pillars:
                    post_data['pillar'] = self.pillars
                if self.environment:
                    post_data['environment'] = self.environment
                self.call(post_data)
