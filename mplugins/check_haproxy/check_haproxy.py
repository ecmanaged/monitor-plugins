#!/usr/bin/env python

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'plugins'))

from __mplugin import MPlugin
from __mplugin import OK, CRITICAL, TIMEOUT



# stdlib
from collections import defaultdict
import re
import time

# 3rd party
import requests

STATS_URL = "/;csv;norefresh"

class HAproxyStatus(MPlugin):

    def get_stats(self):
        url = self.config.get('url', None)
        if not url:
            self.exit(CRITICAL, message="Please provide haproxy status url")
        username = self.config.get('username',None)
        if not username:
            self.exit(CRITICAL, message="Please provide haproxy username")
        password = self.config.get('password')
        if not password:
            self.exit(CRITICAL, message="Please provide haproxy password")

        auth = (username, password)
        url = "%s%s" % (url, STATS_URL)

        r = requests.get(url, auth=auth)

        try:
            r.raise_for_status()
        except Exception as e:
            self.exit(CRITICAL, message=str(e))

        data = r.content.splitlines()

        fields = [f.strip() for f in data[0][2:].split(',') if f]

        data_dict = None

        for line in data[:0:-1]:
            if not line.strip():
                continue
            data_dict = self._line_to_dict(fields, line)

        if not data_dict:
            self.exit(CRITICAL, message="can not obtain stats")

        if 'slim' in data_dict and 'scur' in data_dict:
            try:
                data_dict['spct'] = (data_dict['scur'] / data_dict['slim']) * 100
            except (TypeError, ZeroDivisionError):
                pass

        return data_dict

    def _line_to_dict(self, fields, line):
        data_dict = {}
        for i, val in enumerate(line.split(',')[:]):
            if val:
                try:
                    val = float(val)
                except Exception:
                    pass
                data_dict[fields[i]] = val
        return data_dict

    def run(self):
        data = self.get_stats()

        counter_data = ['stot', 'bin', 'bout', 'dreq', 'dresp', 'ereq', 'econ', 'eresp', 'wretr', 'wredis',
                        'hrsp_1xx', 'hrsp_2xx', 'hrsp_3xx', 'hrsp_4xx', 'hrsp_5xx', 'hrsp_other']
        gauge_data = ['qcur', 'scur', 'slim', 'spct', 'req_rate', 'qtime', 'ctime', 'rtime', 'ttime' ]

        tmp_counter = {}
        for idx in counter_data:
            try:
                tmp_counter[idx] = int(data.get(idx,0))
            except:
                tmp_counter[idx] = data.get(idx,0)

        tmp_counter = self.counters(tmp_counter,'haproxy')

        tmp_gauge = {}
        for idx in gauge_data:
            try:
                tmp_gauge[idx] = int(data.get(idx,0))
            except:
                tmp_gauge[idx] = data.get(idx,0)

        data = tmp_counter.copy()
        data.update(tmp_gauge)


        metrics = {
            'Queue': {
                'current': data['qcur'],
                'time': data['qtime']
            },
            'Session': {
                'current': data['scur'],
                'limit': data['slim'],
                'pct': data['spct'],
                'rate': data['stot'],
                'time': data['ttime']
            },
            'Bytes': {
                'in rate': data['bin'],
                'out rate': data['bout']
            },
            'Denied': {
                'req rate': data['dreq'],
                'resp rate': data['dresp']
            },
            'Errors': {
                'req rate': data['ereq'],
                'con rate': data['econ'],
                'resp rate': data['eresp']
            },
            'Warnings': {
                'retr rate': data['wretr'],

                ' redis rate': data['wredis']
            },
            'Requests': {
                'rate': data['req_rate']
            },
            'Response': {
                '1xx': data['hrsp_1xx'],
                '2xx': data['hrsp_2xx'],
                '3xx': data['hrsp_3xx'],
                '4xx': data['hrsp_4xx'],
                '5xx': data['hrsp_5xx'],
                'other': data['hrsp_other'],
                'response' :data['rtime']
            },
            'Connnect': {
                'time': data['ctime']
            }
        }

        self.exit(OK, data, metrics)    
                  
if __name__ == '__main__':    
    monitor = HAproxyStatus()
    monitor.run()