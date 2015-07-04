#!/usr/bin/python

__author__ = 'Nicolas'
import t411
import transmissionrpc
import base64
import re
from commandline import CmdLine, command
import time
import filesize
import json
import os

TRANSMISSION_ADDRESS_FILE = 'transmission.json' #This is the file where the transmission server address is stored

#https://api.t411.me/


class TransmissionClient(transmissionrpc.Client):
    """
    A wrapper around the transmission.rpc client that also prompt user for the server
    address, and then stored the answers and reuse it in subsequent constructions.
    """

    def __init__(self):
        """
        Constructor: if not TRANSMISSION_ADDRESS_FILE file, ask address to user
        and save it, otherwise, load the data from the file.
        Then instantiate the Transmission client.
        """
        try:
            with open(TRANSMISSION_ADDRESS_FILE) as address_file:
                connection = json.loads(address_file.read())
                if 'address' not in connection or 'port' not in connection:
                    address, port = self.ask_for_connection()
                else:
                    address = connection['address']
                    port = connection['port']
        except:
            address, port = self.ask_for_connection()

        super(TransmissionClient, self).__init__(address=address, port=int(port))

    @staticmethod
    def ask_for_connection():
        """
        Ask the user for the URL and port of the transmission server
        :return: address and port of the transmission server
        """
        address = raw_input('Please enter transmission RPC address: ')
        port = raw_input('Please enter transmission RPC port: ')

        connection_data = json.dumps({'address': '%s' % address, 'port': '%s' % port})
        with open(TRANSMISSION_ADDRESS_FILE, 'w') as connection_file:
            connection_file.write(connection_data)

        return address, port


class T411Commands(CmdLine):
    """
    This the T411 command line interface
    """

    __result_len_limit__ = 20  # can be adjusted by the limit command

    def __init__(self):
        """
        Constructor: create T411 and transmission client connections.
        """
        super(T411Commands, self).__init__(prompt='T411')

        self.query_filters_names = ('cid',)
        self.result_filters = {'grep': self.grep_results}

        try:
            print 'Connecting to T411'
            self.t411 = t411.T411()
        except Exception as e:
            print 'Could not connect to T411: '+str(e)

        try:
            print 'Connecting to Transmission'
            self.transmission = TransmissionClient()
        except Exception as e:
            print 'Could not connect to Transmission: '+str(e)

        self.clear()

    def get_search_string(self, query, filters):
        """
        Create the T411 API search string

        :param query:   Queried string the user added
        :param filters: The list of filters the user en entered (after pipe symbols)
        :return:        The T411 API post request string
        """

        query = query.replace(' ', '+')

        base_search_string = query+'?offset='+str(self.offset)+'&limit='+str(self.__result_len_limit__)

        query_filters = [(index, filter['type'], filter['arg']) for index, filter in enumerate(filters)
                         if filter['type'] in self.query_filters_names]

        if query_filters:
            for filter in query_filters:
                base_search_string += '&{!s}={!s}'.format(filter[1], filter[2])

        return base_search_string

    @staticmethod
    def grep_results(results, filter_argument):
        """
        Filter the results by name using the regular expressions
        :param results:         Search result
        :param filter_argument: Regular expression
        :return:    results, but only those for which the name match regexp
        """

        filter = re.compile(filter_argument[0])

        filtered_result = dict()

        filtered_result['total'] = results['total']
        filtered_result['torrents'] = [torrent for torrent in results['torrents'] if filter.search(torrent['name'])]

        return filtered_result

    def print_search_results(self):
        """
        Display the last search results on screen.
        """

        print 'Found {!s} torrent'.format(self.last_search_result['total'])
        if self.last_search_result:
            for i, torrent in enumerate(self.last_search_result['torrents']):
                print '\t-{!s} {} [{!s} -{!s}-]\t seeders:{!s}\t size = {!s}b'.format(i,
                                                                        torrent['name'].encode('utf-8'),
                                                                        torrent['categoryname'].encode('utf-8'),
                                                                        torrent['category'],
                                                                        torrent['seeders'],
                                                                        filesize.size(int(torrent['size'])))
        else:
            print 'Nothing found.'

    def search_t411(self, filters):
        """
        Initiate a search on T411 and filters the results
        :param filters:     Filters to apply to the search
        :return:
        """
        query_result = self.t411.search(self.get_search_string(self.last_query_string, filters)).json()

        for filter in filters:
            if filter['type'] in self.result_filters:
                query_result = self.result_filters[filter['type']](query_result, filter['arg'])

        return query_result

    @command('reset')
    def reset(self, cmdArgs, filters):
        """
            Reset saved settings (credentials and addresses).
            Accepted arguments are:
            [t411] -> to reset t411 credentials
            [transmission] ->  to reset transmission server address
        """
        if cmdArgs.lower() == 't411':
            os.remove(t411.USER_CREDENTIALS_FILE)
        elif cmdArgs.lower() == 'transmission':
            os.remove(TRANSMISSION_ADDRESS_FILE)

    @command('clear')
    def clear(self, *args):
        """
        Clear previous search results
        """
        self.offset = 0
        self.last_search_result = dict()
        self.last_query_string = ''
        self.last_query_filters = ''

    @command('limit')
    def limit(self, cmdArgs, filters):
        """
        set limit on query result (default is 20, argument is new limit)
        """
        if cmdArgs:
            try:
                self.__result_len_limit__ = int(cmdArgs)
            except:
                pass

        print 'Query limited to {!s} results.'.format(self.__result_len_limit__)

    @command('search')
    def search(self, cmdArgs, filters):
        """
            [query string] -> Search Torrent
            accept filters: cid [category_id] or grep [name regex filter]
            for example: search avatar | cid 5 | grep ava[1-2]
        """
        self.last_query_string = str(cmdArgs)
        self.last_query_filters = filters
        self.last_search_result = self.search_t411(filters)

        self.print_search_results()

    @command('info')
    def info(self, cmdArgs, filters):
        """
        [torrentID] -> Get Torrent Info
        """

        infos = self.t411.details(self.last_search_result['torrents'][int(cmdArgs)]['id']).json()

        for key, value in infos['terms'].iteritems():
            print '\t- ' + key.encode('utf-8') + ':\t' + value.encode('utf-8')

    @command('user')
    def user(self, cmdArgs, filters):
        """
        Show user data (ratio...)
        """

        infos = self.t411.me().json()

        print 'Uploaded: \t' + filesize.size(int(infos['uploaded']))+'b'
        print 'Downloaded: \t' + filesize.size(int(infos['downloaded']))+'b'
        print 'Ratio:\t{:.2f}'.format(float(infos['uploaded'])/float(infos['downloaded']))

    @command('next')
    def next(self, cmdArgs, filterss):
        """
         Shows next results for last query
        """
        if self.last_search_result:
            self.offset += self.__result_len_limit__

            self.last_search_result = self.search_t411(self.last_query_filters)

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

            self.last_search_result = self.search_t411(self.last_query_filters)

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

    def get_download_list(self, cmdArgs):
        """
        Return a list of indexes in the last search result that are selected by the user.
        """

        if cmdArgs.lower() == 'all':

            download_index_list = [torrent['id']for torrent in self.last_search_result['torrents']]

        else:

            from_to_format = re.compile(r'[\s]*(?P<start>[\d]+)[\s]*\-[\s]*(?P<end>[\d]+)[\s]*')
            from_to = re.match(from_to_format, cmdArgs)
            if from_to:
                download_index_list = map(str, range(int(from_to.group('start')), int(from_to.group('end'))+1))
            else:
                download_index_list = cmdArgs.split(',')

        if len(download_index_list) > 1:
            if not CmdLine.confirm("Are you want to download the {!s} torrents".format(len(download_index_list))):
                download_index_list = list()

        return map(int, download_index_list)

    @command('download')
    def download(self, cmdArgs, filters):
        """
            Download torrent. Accepted arguments are:
            ["all"] -> download all results
            [X,Y] -> download torrents with result indexes X and Y.
            [X-Y] -> download torrents with result indexes from X to Y.
            [X] -> download torrents with result indexes X.
        """

        download_index_list = self.get_download_list(cmdArgs)

        for index in download_index_list:

            try:
                torrent = self.t411.download(self.last_search_result['torrents'][index]['id'])

                #with open('temp.torrent', 'w') as torrent_file:
                #    torrent_file.write(torrent.content)

                self.transmission.add_torrent(base64.b64encode(torrent.content))

                time.sleep(1)

            except Exception as e:
                print 'Could not add torrent {!s} to download queue [{!s}]'.\
                        format(self.last_search_result['torrents'][index]['name'].encode('utf-8'), e)
            else:
                print 'successfully added torrent {!s} to download queue'\
                    .format(self.last_search_result['torrents'][index]['name'].encode('utf-8'))

if __name__ == '__main__':

    cli = T411Commands()

    cli.run()

