__author__ = 'Nicolas'
import t411
import os
import transmissionrpc
import base64
import inspect
import re
from commandline import cmdline, command

#https://api.t411.me/

class T411Commands(cmdline):

    __result_len_limit__ = 20

    def __init__(self):
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
            self.transmission = transmissionrpc.Client(address='nicorasp.local', port=9091)
        except Exception as e:
            print 'Could not connect to Transmission: '+str(e)

        self.clear()

        print 'Type \'help\' for help'

    def get_search_string(self, query, filters):

        base_search_string = query+'?offset='+str(self.offset)+'&limit='+str(self.__result_len_limit__)

        query_filters = [(index, filter['type'], filter['arg']) for index, filter in enumerate(filters)
                         if filter['type'] in self.query_filters_names]

        if query_filters:
            for filter in query_filters:
                base_search_string += '&{!s}={!s}'.format(filter[1], filter[2])

        return base_search_string

    @staticmethod
    def grep_results(results, filter_argument):

        filter = re.compile(filter_argument[0])

        filtered_result = dict()

        filtered_result['total'] = results['total']
        filtered_result['torrents'] = [torrent for torrent in results['torrents'] if filter.search(torrent['name'])]

        return filtered_result

    def print_search_results(self):

        print 'Found {!s} torrent'.format(self.last_search_result['total'])
        if self.last_search_result:
            for i, torrent in enumerate(self.last_search_result['torrents']):
                print '\t-{!s} {} [{!s} -{!s}-]\t seeders:{!s}'.format(i,
                                                        torrent['name'].encode('utf-8'),
                                                        torrent['categoryname'].encode('utf-8'),
                                                        torrent['category'],
                                                        torrent['seeders'])
        else:
            print 'Nothing found.'

    def search_t411(self, filters):
        query_result = self.t411.search(self.get_search_string(self.last_query_string, filters)).json()

        for filter in filters:
            if filter['type'] in self.result_filters:
                query_result = self.result_filters[filter['type']](query_result, filter['arg'])

        return query_result

    @command('clear')
    def clear(self, *args):
        """
        Clear previous results
        """
        self.offset = 0
        self.last_search_result = dict()
        self.last_query_string = ''
        self.last_query_filters = ''

    @command('limit')
    def limit(self, cmdArgs, filters):
        """
        set query limit
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

        if cmdArgs.lower == 'all':

            download_index_list = [torrent['id']for torrent in self.last_search_result['torrents']]

        else:

            from_to_format = re.compile(r'[\s]*(?P<start>[\d]+)[\s]*\-[\s]*(?P<end>[\d]+)[\s]*')
            from_to = re.match(from_to_format, cmdArgs)
            if from_to:
                download_index_list = map(str, range(int(from_to.group('start')), int(from_to.group('end'))+1))
            else:
                download_index_list = cmdArgs.split(',')

        if len(download_index_list) > 1:
            if not cmdline.confirm("Are you want to download the {!s} torrents".format(len(download_index_list))):
                download_index_list = list()

        return map(int, download_index_list)

    @command('download')
    def download(self, cmdArgs, filters):
        """
            [search result index] -> Download torrent
            TODO: more complex download pattern
        """

        download_index_list = self.get_download_list(cmdArgs)

        for index in download_index_list:

            try:
                torrent = self.t411.download(self.last_search_result['torrents'][index]['id'])

                #with open('temp.torrent', 'w') as torrent_file:
                #    torrent_file.write(torrent.content)

                self.transmission.add_torrent(base64.b64encode(torrent.content))
            except Exception as e:
                print 'Could not add torrent {!s} to download queue [{!s}]'.\
                        format(self.last_search_result['torrents'][index]['name'].encode('utf-8'), e)
            else:
                print 'successfully added torrent {!s} to download queue'\
                    .format(self.last_search_result['torrents'][index]['name'].encode('utf-8'))

if __name__ == '__main__':

    cli = T411Commands()

    cli.run()

