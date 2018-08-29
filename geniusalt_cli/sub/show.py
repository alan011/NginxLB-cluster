from .common import Handler

class Show(Handler):
    def show(self):
        supported_options = ['-n', '-m', '-i', '--short', '--instance']
        if not self.argParse(supported_options):
            self.error(self.argParseError)

        post_data = {'longTerms': ['--commandline']}
        trigger = 0
        if '-n' in self.args:
            trigger += 1
            post_data['object'] = 'node'
            if self.show_short:
                post_data['longTerms'].append('--short')

            if self.nodes:
                for name in self.nodes:
                    post_data['name'] = name
                    self.call(post_data)
            else:
                self.call(post_data)

        if '-m' in self.args:
            trigger += 1
            post_data['object'] = 'module'
            if self.show_short:
                post_data['longTerms'].append('--short')
            elif self.show_instances:
                post_data['longTerms'].append('--instance')
            if self.modules:
                for name in self.modules:
                    post_data['name'] = name
                    self.call(post_data)
            else:
                self.call(post_data)

        if '-i' in self.args:
            trigger += 1
            post_data['object'] = 'instance'
            if self.show_short:
                post_data['longTerms'].append('--short')
            if self.instances:
                for name in self.instances:
                    post_data['name'] = name
                    self.call(post_data)
            else:
                self.call(post_data)

        if trigger == 0:
            for obj_type in ['node', 'module', 'instance']:
                post_data = {'longTerms': ['--commandline']}
                print("===> %ss:" % obj_type.replace(obj_type[0], obj_type[0].upper(), 1))
                post_data['object'] = obj_type
                if self.show_short:
                    post_data['longTerms'].append('--short')
                elif self.show_instances and obj_type == 'module':
                    post_data['longTerms'].append('--instance')
                self.call(post_data)
    def showb(self):
        supported_options = ['-m', '-i', '--short']
        if not self.argParse(supported_options):
            self.error(self.argParseError)
        if not (self.modules or self.instances):
            self.error("ERROR: Option '-m' or '-i' must be specified.")
        if self.modules and self.instances:
            self.error("ERROR: Option '-m' and '-i' cannot be specified at the same time.")

        post_data = {'longTerms': ['--commandline']}
        if self.show_short:
            post_data['longTerms'].append('--short')
        if self.modules:
            post_data['object'] = 'module'
            if len(self.modules) != 1:
                self.error("ERROR: Multi-objects specification is not allow with 'showb' command.")
            post_data['name'] = self.modules[0]
            self.call(post_data)
        if self.instances:
            post_data['object'] = 'instance'
            if len(self.instances) != 1:
                self.error("ERROR: Multi-objects specification is not allow with 'showb' command.")
            post_data['name'] = self.instances[0]
            self.call(post_data)
