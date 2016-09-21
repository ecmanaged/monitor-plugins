#!/usr/bin/env python

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'plugins'))

from __mplugin import MPlugin
from __mplugin import OK, WARNING, CRITICAL, UNKNOWN, TIMEOUT

import urllib
import socket
from time import time

class CheckURL(MPlugin):
    def run(self):
        url = self.config.get('url')
        content = ''
        if not url:
           self.exit(CRITICAL, message="Invalid URL")
        
        # Set timeout
        timeout = self.config.get('timeout',TIMEOUT)
        socket.setdefaulttimeout(int(timeout))

        start_time = time();
        
        # Fetch
        try:
            urlopen = urllib.urlopen(url)

        except:
            self.exit(CRITICAL, message="Unable to open URL")
        
        end_time = time()
        mytime = "%.2f" %(end_time - start_time)
        
        # Get size
        size = 0
        headers = urlopen.info()
        content = ''.join(urlopen.readlines())
        
        if "content-length" in headers:
            size = int(headers["Content-Length"])
        
        else:
            size = len(content)
        
        data = {
            'content': content,
            'code': urlopen.getcode(),
            'size': size,
            'time': mytime
        }
        
        metrics = {
            'Content Size': {
              'size': str(size) + 'B'
            },
            'Response time': {
              'time': str(mytime) + 's'
            }
        }
        
        urlopen.close()
        self.exit(OK,data,metrics)
        
        
monitor = CheckURL()
monitor.run()
