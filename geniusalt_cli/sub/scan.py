from .common import Handler

class Scan(Handler):
    def scan(self):
        supported_options = ['-n', '-m']

        if not self.argParse(supported_options):
            self.error(self.argParseError)
        if not ('-n' in self.args or '-m' in self.args):
            self.error("ERROR: Action 'scan' requires at least one option in '-n' or '-m'.")

        if '-n' in self.args:
            post_data = {'object': 'node'}
            self.call(post_data)

        if '-m' in self.args:
            post_data = {'object': 'module'}
            self.call(post_data)
