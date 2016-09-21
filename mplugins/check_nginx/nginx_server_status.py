#!/usr/bin/env python

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'plugins'))

from __mplugin import MPlugin
from __mplugin import OK, CRITICAL, TIMEOUT

import socket, urllib, re

class NginxStatus(MPlugin):
    def run(self):
        url = self.config.get('url')
        if not url:
           self.exit(CRITICAL, message="Please specify URL")

        # Fetch URL
        url_open = None
        try:
            url_open = urllib.urlopen(url)
        except:
            self.exit(CRITICAL, message="Unable to open URL")

        if not url_open or url_open.getcode() != 200:
            self.exit(CRITICAL, message="Can not reach URL")

        # Set timeout
        timeout = self.config.get('timeout',TIMEOUT)
        socket.setdefaulttimeout(int(timeout))

        data = self._get_data(url_open)

        counter_data = [
            'accepted',
            'handled',
            'requests'
        ]
        
        gauge_data = [
            'connections',
            'reading',
            'writing',
            'waiting'           
        ]
        
        tmp_counter = {}
        for idx in counter_data:
            try:
                tmp_counter[idx] = int(data.get(idx,0))
            except:
                tmp_counter[idx] = data.get(idx,0)
        
        tmp_counter = self.counters(tmp_counter,'nginx')
      
        tmp_gauge = {}
        for idx in gauge_data:
            try:
                tmp_gauge[idx] = int(data.get(idx,0))
            except:
                tmp_gauge[idx] = data.get(idx,0)
                        
        data = tmp_counter.copy()
        data.update(tmp_gauge)

        metrics = {
            'Connections': {
                'connections': data['connections'],
                'Accepted': data['accepted'],
                'Handled': data['handled']
            },
            'Request per second': {
                'requests': data['requests']
            },
            'Scoreboard': {
                'reading': data['reading'],
                'writing': data['writing'],
                'waiting': data['waiting']
            }
        }
        self.exit(OK, data, metrics)

    def _get_data(self, url):
        data = url
        data = data.read()
        result = {}
        match1 = re.search(r'Active connections:\s+(\d+)', data)
        match2 = re.search(r'\s*(\d+)\s+(\d+)\s+(\d+)', data)
        match3 = re.search(r'Reading:\s*(\d+)\s*Writing:\s*(\d+)\s*'
                             'Waiting:\s*(\d+)', data)

        if not match1 or not match2 or not match3:
            self.exit(CRITICAL, message='Unable to parse. Make sure that you have provided the nginx_stat page url.')

        result['connections'] = int(match1.group(1))
        result['accepted'] = int(match2.group(1))
        result['handled'] = int(match2.group(2))
        result['requests'] = int(match2.group(3))
        result['reading'] = int(match3.group(1))
        result['writing'] = int(match3.group(2))
        result['waiting'] = int(match3.group(3))
        return result
    
monitor = NginxStatus()
monitor.run()
