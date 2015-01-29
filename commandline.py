__author__ = 'Nicolas'
import inspect

def command(command_string):
    def decorator(func):
        func.command_string = command_string
        return func

    return decorator

class cmdline(object):



    def __init__(self, prompt):

        self.prompt = prompt
        self.__load_commands()
        self.__create_menu()

        print 'Type \'help\' for help'

    def __load_commands(self):
        self.commands = {method[1].command_string:  {'method': method[1], 'doc': inspect.getdoc(method[1])}
                         for method in inspect.getmembers(self, predicate=inspect.ismethod)
                         if hasattr(method[1], 'command_string')}

    def __create_menu(self):

        self.menu = 'T411:\n'

        for str, cmd in self.commands.iteritems():

            try:
                doclines = cmd['doc'].splitlines()
                self.menu += '\t-{:<10}:\t{!s}\n'.format(str, doclines[0])

                if len(doclines)>1:
                    for line in doclines[1:]:
                        self.menu += '              \t{!s}\n'.format(line)
            except:
                self.menu += '\t-{!s}\n'.format(str)

    @command('quit')
    def quit(self, cmdArgs, filters):
        pass

    @staticmethod
    def confirm(question):

        answer = raw_input(question+ ' (Y/N): ')

        return answer.lower() == 'y'

    def __prompt(self):
        return raw_input(self.prompt + ': ')

    @command('help')
    def help(self, cmdArgs, filters):
        print self.menu

    @staticmethod
    def parse_command_line(line):

        filters = list()
        cmdArgs = ''
        cmd = ''

        for i, ele in enumerate(line.split('|')):
            if i:
                filters.append({'type': (ele.split())[0], 'arg': (ele.split())[1:]})
            else:
                cmd = (ele.split())[0]

                if len(ele.split())>1:
                    cmdArgs = (ele.split())[1:][0]

        return cmd, cmdArgs, filters

    def run(self):

        cmd = ''

        while cmd != 'quit':

            cmd, cmdArgs, filters = self.parse_command_line(self.__prompt())

            try:
                self.commands[cmd]['method'](cmdArgs, filters)
            except KeyError as e:
                print 'Command {!s} not recognized-{!s}-'.format(cmd, e)
            except Exception as e:
                print 'Command {!s} failed -{!s}-'.format((cmd.split())[1:], e)