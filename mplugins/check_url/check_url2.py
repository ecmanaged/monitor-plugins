#!/usr/bin/env python

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'plugins'))

from __mplugin import MPlugin
from __mplugin import OK, WARNING, CRITICAL, UNKNOWN, TIMEOUT

import urllib
import urllib2
import socket
import json
from time import time

class CheckURL(MPlugin):
    def run(self):
        url = self.config.get('url')
        method = self.config.get('method')
        headers_raw = self.config.get('headers')
        data_raw = self.config.get('data')

        if not url:
           self.exit(CRITICAL, message="Invalid URL")

        headers = {}

        if headers_raw:
            headers_list = headers_raw.split(',')
            for item in headers_list:
                key, value = item.split(':')
                headers[key.strip()] = value.strip()

        data = {}

        if data_raw:
            try:
                data = json.loads(data_raw)
            except:
                data_list = data_raw.split(',')
                for item in data_list:
                    key, value = item.split(':')
                    data[key.strip()] = value.strip()

        # Set timeout
        timeout = self.config.get('timeout',TIMEOUT)
        socket.setdefaulttimeout(int(timeout))

        if method == 'POST':

            if not data:
                self.exit(CRITICAL, message="Unable to parse data to POST")

            start_time = time()

            try:
                if headers:
                    content_type = headers.get("Content-Type", None)
                    if content_type == 'application/json':
                        req = urllib2.Request(url, json.dumps(data), headers)
                    else:
                        req = urllib2.Request(url, urllib.urlencode(data), headers)
                else:
                    req = urllib2.Request(url, urllib.urlencode(data))
                urlopen = urllib2.urlopen(req)
            except:
                self.exit(CRITICAL, message="Unable to POST to open URL")

            end_time = time()
            mytime = "%.2f" %(end_time - start_time)

            # Get size
            size = 0
            headers = urlopen.info()
            content = ''.join(urlopen.readlines())
            code = urlopen.getcode()

            if "content-length" in headers:
                size = int(headers["Content-Length"])
            else:
                size = len(content)
            urlopen.close()

        else:
            # Default is GET
            start_time = time()
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
            code = urlopen.getcode()

            if "content-length" in headers:
                size = int(headers["Content-Length"])
            else:
                size = len(content)
            urlopen.close()

        data = {
            'content': content,
            'code': code,
            'size': size,
            'time': mytime
        }

        metrics = {
            'Content Size': {
              'size': size
            },
            'Response time': {
              'time': mytime
            }
        }

        self.exit(OK,data,metrics)


monitor = CheckURL()
monitor.run()