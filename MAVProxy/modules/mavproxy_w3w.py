#!/usr/bin/env python
'''
Example Module
Peter barker, September 2016

This module simply serves as a starting point for your own MAVProxy module.

1. copy this module sidewise (e.g. "cp mavproxy_example.py mavproxy_coolfeature.py"
2. replace all instances of "example" with whatever your module should be called
(e.g. "coolfeature")

3. trim (or comment) out any functionality you do not need
'''

import os
import os.path
import sys
from pymavlink import mavutil
import errno
import time
import json

from MAVProxy.modules.lib import mp_module
from MAVProxy.modules.lib import mp_util
from MAVProxy.modules.lib import mp_settings


if sys.version_info.major < 3:
    # from urllib2 import Request as url_request
    from urllib2 import urlopen as url_open
    # from urllib2 import URLError as url_error
else:
    # from urllib.request import Request as url_request
    from urllib.request import urlopen as url_open
    # from urllib.error import URLError as url_error


class w3w(mp_module.MPModule):
    def __init__(self, mpstate):
        """Initialise module"""
        super(w3w, self).__init__(mpstate, "w3w", "what3words global addressing")

        self.requests_successful = 0
        self.requests_failed = 0

        self.position = (0, 0)
        self.bounds = None
        self.words = 'UNKNOWN'

        self.w3w_settings = mp_settings.MPSettings(
            [ ('verbose', bool, False),
              ('key', str, '')
          ])
        self.add_command('w3w', self.cmd_w3w, "what3words module", ['status', 'set (LOGSETTING)', 'get_words'])

    def usage(self):
        '''show help on command line options'''
        return "Usage: w3w <status|set|get_words>"

    def address(self):
        return "Current address ///{}".format(self.words)

    def cmd_w3w(self, args):
        '''control behaviour of the module'''
        if len(args) == 0:
            print(self.usage())
        elif args[0] == "status":
            print(self.status())
        elif args[0] == "set":
            self.w3w_settings.command(args[1:])
        elif args[0] == "get_words":
            self.get_words(self.position[0], self.position[1])
            if self.w3w_settings.verbose:
                print (self.address())
        else:
            print(self.usage())

    def update_address(self):
        need_update = True
        try:
            if self.bounds[u'southwest'][u'lat'] < self.position[0] < self.bounds[u'northeast'][u'lat'] and \
               self.bounds[u'southwest'][u'lng'] < self.position[1] < self.bounds[u'northeast'][u'lng']:
                need_update = False
        except Exception as e:
            need_update = True

        if need_update:
            self.get_words(self.position[0], self.position[1])
        # else:
        #     print ('update unnecessary')

    def get_words(self, lat, lon):
        d = json.loads(url_open('https://api.what3words.com/v2/reverse?coords={}%2C{}&key={}'
                                .format(lat, lon, self.w3w_settings.key),
                                timeout=2).read())
        self.words = d['words']
        self.bounds = d['bounds']

    def status(self):
        '''returns information about module'''
        return "Current position {} address ///{}".format(self.position, self.words)

    def idle_task(self):
        '''called rapidly by mavproxy'''
        pass

    def mavlink_packet(self, msg):
        '''handle mavlink packets'''
        msg_type = msg.get_type()
        if msg_type == 'GLOBAL_POSITION_INT':
            old_words = self.words

            self.position = (float(msg.lat) / 10000000, float(msg.lon) / 10000000)
            self.update_address()

            if self.w3w_settings.verbose:
                if old_words != self.words:
                    print (self.address())


def init(mpstate):
    '''initialise module'''
    return w3w(mpstate)
