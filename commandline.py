__author__ = 'Nicolas'
import inspect

def command(command_string):
    """
    Decorator for commands (command_string is the command itself)
    """
    def decorator(func):
        func.command_string = command_string
        return func

    return decorator


class CmdLine(object):
    """
    A class to easily create command line interface:
    simply decorate commands with the @command operator
    """

    def __init__(self, prompt):
        """
        Constructor
        """

        self.prompt = prompt
        self.__load_commands()
        self.__create_menu()

        print 'Type \'help\' for help'

    def __load_commands(self):
        """
        Visit all class methods that were decorated to build the command list
        """
        self.commands = {method[1].command_string:  {'method': method[1], 'doc': inspect.getdoc(method[1])}
                         for method in inspect.getmembers(self, predicate=inspect.ismethod)
                         if hasattr(method[1], 'command_string')}

    def __create_menu(self):
        """
        Create a help menu from the doc string of the decorated command methods
        """
        self.menu = 'T411:\n'

        for str, cmd in self.commands.iteritems():

            try:
                doclines = cmd['doc'].splitlines()
                self.menu += '\t-{:<10}:\t{!s}\n'.format(str, doclines[0])

                if len(doclines) > 1:
                    for line in doclines[1:]:
                        self.menu += '              \t{!s}\n'.format(line)
            except:
                self.menu += '\t-{!s}\n'.format(str)

    @command('quit')
    def quit(self, cmdArgs, filters):
        """
        This is the command to quit.
        """
        pass

    @staticmethod
    def confirm(question):
        """
        Ask user a question, return True if the answer is yes, false otherwise.
        """

        answer = raw_input(question + ' (Y/N): ')

        return answer.lower() == 'y'

    def __prompt(self):
        return raw_input(self.prompt + ': ')

    @command('help')
    def help(self, cmdArgs, filters):
        print self.menu

    @staticmethod
    def parse_command_line(line):
        """
        Parse the command line and extract:
        - The command
        - its arguments
        - Its filters
        Format is "cmd cmdArg | filter1 arg | filter2 arg"
        """

        filters = list()
        cmdArgs = ''
        cmd = ''

        for i, ele in enumerate(line.split('|')):
            if i:
                filters.append({'type': (ele.split())[0], 'arg': (ele.split())[1:]})
            else:

                if len(ele.split()) > 0:
                    cmd = (ele.split())[0]
                    cmdArgs = ' '.join(ele.split()[1:])

        return cmd, cmdArgs, filters

    def run(self):
        """
        CLI loop
        """

        cmd = ''

        while cmd != 'quit':

            cmd, cmdArgs, filters = self.parse_command_line(self.__prompt())

            try:
                self.commands[cmd]['method'](cmdArgs, filters)
            except KeyError as e:
                print 'Command {!s} not recognized-{!s}-'.format(cmd, e)
            except Exception as e:
                print 'Command {!s} failed -{!s}-'.format((cmd.split())[1:], e)