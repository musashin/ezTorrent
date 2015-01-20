__author__ = 'Nicolas'
import t411
import os
import transmissionrpc
import base64

#https://api.t411.me/

class cmdLoop:

    __result_len_limit__ = 20

    def __init__(self):

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

    def clear(self, *args):
        self.offset = 0
        self.last_search_result = dict()
        self.last_query_string = ''

    def __main_menu(self):

        print 'Choose between'
        print '\t-\'s\'\tSearch'
        print '\t-\'d\'\tDownload'
        print '\t-\'n\'\tNext'
        print '\t-\'p\'\tPrevious'
        print '\t-\'c\'\tClear'
        print '\t-\'i\'\tInfo'
        print '\t-\'i\'\tUser'
        print '\t-\'q\'\tQuit'
        return raw_input('Prompt: ')

    def get_search_string(self, query):

        return query+'?offset='+str(self.offset)+'&limit='+str(self.__result_len_limit__)

    def print_search_results(self):
        if self.last_search_result:
            for i, torrent in enumerate(self.last_search_result['torrents']):
                print '\t-{!s} {}'.format(i, torrent['name'].encode('utf-8'))
        else:
            print 'Nothing found.'

    def search_t411(self):
        return self.t411.search(self.get_search_string(self.last_query_string)).json()

    def search(self, *args):

        self.last_query_string = str(*args[0])
        self.last_search_result = self.search_t411()

        self.print_search_results()

    def info(self, *args):

        infos =  self.t411.details(self.last_search_result['torrents'][int(*args[0])]['id']).json()

        for key, value in infos['terms'].iteritems():
            print '\t- ' + key + ':\t' + value

    def user(self, *args):
        infos = self.t411.me().json()

        print 'Uploaded:\t'+str(infos['uploaded'])+' bytes'
        print 'Downloaded:\t'+str(infos['downloaded'])+' bytes'
        print 'Ratio:\t'+str(float(infos['uploaded'])/float(infos['downloaded']))

    def next(self, *args):
        if self.last_search_result:
            self.offset += self.__result_len_limit__

            self.last_search_result = self.search_t411()

            self.print_search_results()
        else:
            print 'You need to make a search first.'

    def previous(self, *args):
        if self.last_search_result:
            self.offset -= self.__result_len_limit__

            self.offset = max(0, self.offset)

            self.last_search_result = self.search_t411()

            self.print_search_results()
        else:
            print 'You need to make a search first.'

    def download(self, *args):

        torrent = self.t411.download(self.last_search_result['torrents'][int(*args[0])]['id'])

        self.transmission.add_torrent(base64.b64encode(torrent.content))

    def run(self):

        choice = ''
        actions = {'s': self.search,
                   'd': self.download,
                   'n': self.next,
                   'p': self.previous,
                   'c': self.clear,
                   'i': self.info,
                   'u': self.user}

        while choice != 'q':

            choice = self.__main_menu()

            try:
                actions[(choice.split())[0]]((choice.split())[1:])
            except KeyError as e:
                print 'Command {!s} not recognized'.format(choice)
            except Exception as e:
                print 'Command {!s} failed -{!s}-'.format((choice.split())[1:],e)



if __name__ == '__main__':

    cli = cmdLoop()

    cli.run()

