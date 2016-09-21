#!/usr/bin/env python

import socket, urllib, re

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'plugins'))

from __mplugin import MPlugin
from __mplugin import OK, CRITICAL


class PhPFPMStatus(MPlugin):
    
    def get_stats(self):

        url = self.config.get('url')

        if not url:
            self.exit(CRITICAL, message="Please Specify URL")

        
        if (re.search("\?html$", url)) or re.search("\?xml$", url) or re.search("\?full$", url) or (re.search("\&full$", url)):
            self.exit(CRITICAL, message="Invalid URL, we accept url like this domain.com/status/?json")

        if not re.search("\?json$", url):
            url = url + '?json'
            
        try:
            urlopen = urllib.urlopen(url)
        except:
            self.exit(CRITICAL, message="Invalid URL")

        data = self._from_json(urlopen.read())

        if not data:
            self.exit(CRITICAL, message="Unable to parse statistics")

        return data
    
    def run(self):
        data = self.get_stats()

        counter_data = [
            'accepted conn'
        ]

        gauge_data = [
            'active processes',
            'idle processes',
            'max active processes',

            'max children reached',

            'listen queue len',
            'max listen queue',
            'listen queue',

            'slow requests'
        ]
        
        tmp_counter = {}
        for idx in counter_data:
            try:
                tmp_counter[idx] = int(data.get(idx,0))
            except:
                tmp_counter[idx] = data.get(idx,0)
        
        tmp_counter = self.counters(tmp_counter,'phpfpm')
      
        tmp_gauge = {}
        for idx in gauge_data:
            try:
                tmp_gauge[idx] = int(data.get(idx,0))
            except:
                tmp_gauge[idx] = data.get(idx,0)
                        
        data = tmp_counter.copy()
        data.update(tmp_gauge)
    
        metrics = {
            'Processes Statistics': {
              'active processes': data['active processes'],
              'idle processes': data['idle processes'],
              'max active processes': data['max active processes']
            },
            'max children reached': {
              'max children reached': data['max children reached']
            },
            'queue statistics': {
              'listen queue len': data['listen queue len'],
              'max listen queue': data['max listen queue'],
              'listen queue': data['listen queue']
            },
            'slow requests': {
              'slow requests': data['slow requests']
            }
        }
        
        self.exit(OK, data, metrics)

if __name__ == '__main__':    
    monitor = PhPFPMStatus()
    monitor.run()