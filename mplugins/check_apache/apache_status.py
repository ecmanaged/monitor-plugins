#!/usr/bin/env python

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'plugins'))

from __mplugin import MPlugin
from __mplugin import OK, CRITICAL, TIMEOUT

import socket
import urllib


class ApacheStatus(MPlugin):
    def run(self):
        url = self.config.get('url')

        if not url:
            self.exit(CRITICAL, message="Invalid URL")

        # Add auto to server-status url
        if not url.endswith('?auto'):
            url = url + '?auto'

        # Set timeout
        socket.setdefaulttimeout(self.config.get('timeout', TIMEOUT))

        # Fetch URL
        try:
            urlopen = urllib.urlopen(url)
        except:
            self.exit(CRITICAL, message="Unable to open URL")

        if urlopen.getcode() != 200:
            self.exit(CRITICAL, message="Unable to open URL")

        data = self._parse_status(urlopen.readlines())

        metrics = {
            'Apache Workers': {
                'busy_workers': data['busy_workers'],
                'idle_workers': data['idle_workers']
            },
            'Request per second': {
                'requests_per_second': data['requests_per_second']
            },
            'Scoreboard': {
                'Waiting': data['waiting_for_connection'],
                'Starting': data['starting_up'],
                'Reading': data['reading_request'],
                'Sending': data['sending_reply'],
                'Keepalive': data['keepalive'],
                'DNS Lookup': data['dns_lookup'],
                'Closing': data['closing_connection'],
                'Logging': data['logging'],
                'Finishing': data['gracefully_finishing'],
                'Idle': data['idle_cleanup_of_worker'],
                'Open slots': data['open_slots']
            },
            'Bytes per second': {
                'bytes_per_second': data['bytes_per_second']
            },
            'CPU Load': {
                'cpuload': data['cpuload']
            }
        }
        self.exit(OK, data, metrics)

    def _parse_status(self, raw):
        # Initialize with None because mod_status has different levels of
        # verbosity. So if it doesn't respond with a value, we'll just have
        # a None instead which is nicer than getting unpredictable exceptions
        # when accessing the output later on.

        parsed = {
            'total_accesses': None,
            'total_kbytes': None,
            'cpuload': None,
            'uptime': None,
            'requests_per_second': None,
            'bytes_per_second': None,
            'bytes_per_request': None,
            'busy_workers': None,
            'idle_workers': None,
            'waiting_for_connection': None,
            'starting_up': None,
            'reading_request': None,
            'sending_reply': None,
            'keepalive': None,
            'dns_lookup': None,
            'closing_connection': None,
            'logging': None,
            'gracefully_finishing': None,
            'idle_cleanup_of_worker': None,
            'open_slots': None
            }

        # Do the nasty parsing. Doing this programatically may be
        # more extensible but it's much rougher looking.

        # Old python compat
        if self._is_list(raw):
            raw = '\n'.join(raw)

        for line in str(raw).splitlines():
            if not line:
                continue

            if ': ' not in line:
                continue

            (key, value) = line.split(': ')
            if key == 'Total Accesses':
                parsed['total_accesses'] = self.counter(int(value), 'total_accesses')

            if key == 'Total kBytes':
                parsed['total_kbytes'] = self.counter(int(value), 'total_kbytes')

            if key == 'CPULoad':
                parsed['cpuload'] = float(value)

            if key == 'Uptime':
                parsed['uptime'] = int(value)

            if key == 'ReqPerSec':
                parsed['requests_per_second'] = float(value)

            if key == 'BytesPerSec':
                parsed['bytes_per_second'] = float(value)

            if key == 'BytesPerReq':
                parsed['bytes_per_request'] = float(value)

            if key == 'BusyWorkers':
                parsed['busy_workers'] = int(value)

            if key == 'IdleWorkers':
                parsed['idle_workers'] = int(value)

            if key == 'Scoreboard':
                parsed['waiting_for_connection'] = value.count('_')
                parsed['starting_up'] = value.count('S')
                parsed['reading_request'] = value.count('R')
                parsed['sending_reply'] = value.count('W')
                parsed['keepalive'] = value.count('K')
                parsed['dns_lookup'] = value.count('D')
                parsed['closing_connection'] = value.count('C')
                parsed['logging'] = value.count('L')
                parsed['gracefully_finishing'] = value.count('G')
                parsed['idle_cleanup_of_worker'] = value.count('I')
                parsed['open_slots'] = value.count('.')

        return parsed

if __name__ == '__main__':
    monitor = ApacheStatus()
    monitor.run()
