__author__ = 'Nicolas'
import t411
import os
import transmissionrpc
import base64
import inspect

#https://api.t411.me/

class cmdLoop:

    __result_len_limit__ = 20

    def command(command_string):
        def decorator(func):
            func.command_string = command_string
            return func

        return decorator

    def __init__(self):
        self.__load_commands()
        self.__create_menu()

        try:
            print 'Connecting to T411'
            self.t411 = t411.T411()
        except Exception as e:
            print 'Could not connect to T411: '+str(e)

        try:
            print 'Connecting to Transmission'
            self.transmission = transmissionrpc.Client(address='nicorasp.local', port=9091)
        except Exception as e:
            print 'Could not connect to Transmission: '+str(e)

        self.clear()

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
                self.menu += '\t-{!s}:\t\t{!s}\n'.format(str, doclines[0])

                if len(doclines)>1:
                    for line in doclines[1:]:
                        self.menu += '\t\t\th{!s}\n'.format(line)
            except:
                self.menu += '\t-{!s}\n'.format(str)

    def __main_menu(self):

        return raw_input('T411: ')

    def get_search_string(self, query, filters):

        query_filters_names = ('cid',)

        base_search_string = query+'?offset='+str(self.offset)+'&limit='+str(self.__result_len_limit__)

        query_filters = [(index, filter['type'], filter['arg']) for index, filter in enumerate(filters) if filter['type'] in query_filters_names]

        if query_filters:
            for filter in query_filters:
                base_search_string += '&{!s}={!s}'.format(filter[1], filter[2])

        return base_search_string

    def print_search_results(self):

        print 'Found {!s} torrent'.format(self.last_search_result['total'])
        if self.last_search_result:
            for i, torrent in enumerate(self.last_search_result['torrents']):
                print '\t-{!s} {} [{!s} -{!s}-]'.format(i,
                                                        torrent['name'].encode('utf-8'),
                                                        torrent['categoryname'].encode('utf-8'),
                                                        torrent['category'])
        else:
            print 'Nothing found.'

    def search_t411(self, filters):
        return self.t411.search(self.get_search_string(self.last_query_string, filters)).json()

    @command('clear')
    def clear(self, *args):
        """
        Clear previous results
        """
        self.offset = 0
        self.last_search_result = dict()
        self.last_query_string = ''


    @command('search')
    def search(self, cmdArgs, filters):
        """
            [query string] -> Search Torrent
            accept filters:
                | cuid category_id
        """
        self.last_query_string = str(cmdArgs)
        self.last_search_result = self.search_t411(filters)

        self.print_search_results()

    @command('help')
    def help(self, cmdArgs, filters):
        print self.menu

    @command('info')
    def info(self, cmdArgs, filters):
        """
            [torrentID] -> Get Torrent Info
        """

        infos = self.t411.details(self.last_search_result['torrents'][int(cmdArgs)]['id']).json()

        for key, value in infos['terms'].iteritems():
            print '\t- ' + key + ':\t' + value

    @command('user')
    def user(self, cmdArgs, filters):
        """
        Show user data (ratio...)
        """

        infos = self.t411.me().json()

        print 'Uploaded:\t'+str(infos['uploaded'])+' bytes'
        print 'Downloaded:\t'+str(infos['downloaded'])+' bytes'
        print 'Ratio:\t'+str(float(infos['uploaded'])/float(infos['downloaded']))

    @command('next')
    def next(self, cmdArgs, filterss):
        """
            Shows next results for last query
        """
        if self.last_search_result:
            self.offset += self.__result_len_limit__

            self.last_search_result = self.search_t411()

            self.print_search_results()
        else:
            print 'You need to make a search first.'

    @command('previous')
    def previous(self, cmdArgs, filters):
        """
            Shows previous results for last query
        """
        if self.last_search_result:
            self.offset -= self.__result_len_limit__

            self.offset = max(0, self.offset)

            self.last_search_result = self.search_t411()

            self.print_search_results()
        else:
            print 'You need to make a search first.'

    @command('cat')
    def cat(self, cmdArgs, filters):
        """
            List categories
        """
        cat_list = self.t411.categories().json()

        for cat_id, cat_info in cat_list.iteritems():
            if 'id' in cat_info:

                print '\t-{!s}:\t{!s}'.format(cat_id, cat_info['name'].encode('utf-8'))

                if 'cats' in cat_info:
                    for subcat_id, subcat_info in cat_info['cats'].iteritems():
                        print '\t\t-{!s}:\t{!s}'.format(subcat_id, subcat_info['name'].encode('utf-8'))

    @command('download')
    def download(self, cmdArgs, filters):
        """
            [search result index] -> Download torrent
        """

        torrent = self.t411.download(self.last_search_result['torrents'][int(cmdArgs)]['id'])

        self.transmission.add_torrent(base64.b64encode(torrent.content))

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

        while cmd != 'q':

            cmd, cmdArgs, filters = self.parse_command_line(self.__main_menu())

            try:
                self.commands[cmd]['method'](cmdArgs, filters)
            except KeyError as e:
                print 'Command {!s} not recognized-{!s}-'.format(cmd, e)
            except Exception as e:
                print 'Command {!s} failed -{!s}-'.format((cmd.split())[1:], e)




if __name__ == '__main__':

    cli = cmdLoop()

    cli.run()

