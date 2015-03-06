#! /usr/bin/env python3
# -*- coding: UTF-8 -*-

"""
Python interface for T411.me

Authors : 
 * Arnout Pierre <pierre@arnout.fr>
 * Ackermann Audric <audric.bilb@gmail.com>
"""


from getpass import getpass
from json import loads, dumps  
from requests import post, codes

HTTP_OK = 200
API_URL = 'https://api.t411.io/%s'
USER_CREDENTIALS_FILE = 'user.json'



class T411Exception(BaseException):
    pass

class T411(object):
    """ Base class for t411 interface """

    def __init__(self, username = None, password = None) :
        """ Get user credentials and authentificate it, if any credentials
        defined use token stored in user file
        """

        try :
            with open(USER_CREDENTIALS_FILE) as user_cred_file:
                self.user_credentials = loads(user_cred_file.read())
                if 'uid' not in self.user_credentials or 'token' not in \
                        self.user_credentials:
                    raise T411Exception('Wrong data found in user file')
                #else:
                    # we have to ask the user for its credentials and get
                    # the token from the API
                    #user = raw_input('Please enter username: ')
                    #password = getpass('Please enter password: ')
                    #self._auth(user, password)
        except IOError as e:
            # we have to ask the user for its credentials and get
            # the token from the API
            user = raw_input('Please enter username: ')
            password = getpass('Please enter password: ')
            self._auth(user, password)
        except T411Exception as e:
            raise T411Exception(e.message)
        except Exception as e:
            raise T411Exception('Error while reading user credentials: %s.'\
                    % e.message)

    def _auth(self, username, password) :
        """ Authentificate user and store token """
        self.user_credentials = self.call('auth', {'username': username, 'password': password}).json()
        print(self.user_credentials)
        if 'error' in self.user_credentials:
            raise T411Exception('Error while fetching authentication token: %s'\
                    % self.user_credentials['error'])
        # Create or update user file
        user_data = dumps({'uid': '%s' % self.user_credentials['uid'], 'token': '%s' % self.user_credentials['token']})
        with open(USER_CREDENTIALS_FILE, 'w') as user_cred_file:
            user_cred_file.write(user_data)
        return True

    def call(self, method = '', params = None) :
        """ Call T411 API """
        
        if method != 'auth' :
            req = post(API_URL % method, data=params, headers={'Authorization': self.user_credentials['token']}  )
        else:
            req = post(API_URL % method, data=params)
            
        if req.status_code == codes.OK:
            return req
        else :
            raise T411Exception('Error while sending %s request: HTTP %s' % \
                    (method, req.status_code))

    def me(self) :
        """ Get personal informations """
        return self.call('users/profile/%s' % self.user_credentials['uid'])

    def user(self, user_id) :
        """ Get user informations """
        return self.call('users/profile/%s' % user_id)

    def categories(self) :
        """ Get categories """
        return self.call('categories/tree')

    def terms(self) :
        """ Get terms """
        return self.call('terms/tree')

    def details(self, torrent_id) :
        """ Get torrent details """
        return self.call('torrents/details/%s' % torrent_id)
        
    def search(self, to_search) :
        """ Get torrent results for specific search """
        return self.call('torrents/search/%s' % to_search)    

    def download(self, torrent_id) :
        """ Download a torrent """
        return self.call('torrents/download/%s' % torrent_id)
        
    def top100(self) :
        """ Get top 100 """
        return self.call('/torrents/top/100')
        

    def top_today(self) :
        """ Get top today """
        return self.call('/torrents/top/today')


    def top_week(self) :
        """ Get top week """
        return self.call('/torrents/top/week')

    def top_month(self) :
        """ Get top month """
        return self.call('/torrents/top/month')
        
    def get_bookmarks(self) :
        """ Get bookmarks of user """
        return self.call('/bookmarks')
        
    def add_bookmark(self, torrent_id) :
        """ Get bookmarks of user """
        return self.call('/bookmarks/save/%s' % torrent_id)
         
         
    def delete_bookmark(self, torrent_id) :
        """ Delete a bookmark """
        return self.call('/bookmarks/delete/%s' % torrent_id)


if __name__ == "__main__":
    t411 = T411()
    print(t411.search("Homeland"))
    
    
    
