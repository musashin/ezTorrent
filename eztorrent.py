__author__ = 'Nicolas'
import t411
import os
import transmissionrpc
import base64

class cmdLoop:

    def __init__(self):
        self.t411 = t411.T411()
        self.transmission = transmissionrpc.Client(address='nicorasp.local', port=9091)

    def __main_menu(self):

        print 'Choose between'
        print '\t-\'s\'\tSearch'
        print '\t-\'d\'\tDownload'
        print '\t-\'q\'\tQuit'
        return raw_input('Prompt: ')

    def search(self, argument):

        self.last_search_result = self.t411.search(argument).json()

        for i, torrent in enumerate(self.last_search_result['torrents']):
            print '\t-{!s} {}'.format(i, torrent['name'].encode('utf-8'))

    def download(self, argument):

        if not os.path.exists(r'.\temp'):
            os.makedirs(r'.\temp')

        torrent = self.t411.download(self.last_search_result['torrents'][int(argument)]['id'])

        self.transmission.add_torrent(base64.b64encode(torrent.content))

    def run(self):

        choice = ''
        actions = {'s': self.search, 'd': self.download}

        while choice != 'q':

            choice = self.__main_menu()

            try:
                actions[(choice.split())[0]]((choice.split())[1])
            except Exception as e:
                print 'Command {!s} not recognized'.format(choice)

if __name__ == '__main__':

    cli = cmdLoop()

    cli.run()

