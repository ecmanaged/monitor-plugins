#!/usr/bin/env python

import subprocess
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'plugins'))

from __mplugin import MPlugin
from __mplugin import OK, CRITICAL, TIMEOUT


class VarnishStatus(MPlugin):
    def run(self):
        if not self.which('varnishstat'):
            self.exit(CRITICAL, message="Please install varnish. varnishstat not available")

        raw_data = subprocess.Popen(
            'varnishstat -1 -j',
            shell=True,
            stdout=subprocess.PIPE).stdout.read()

        if not raw_data:
            self.exit(CRITICAL, message='Cannot get status from varnish')

        data = self._parse_data(raw_data)

        counter_data = [
            'MAIN.sess_conn',
            'MAIN.sess_drop',
            'MAIN.sess_fail',
            'MAIN.cache_hit',
            'MAIN.cache_miss',
            'MAIN.backend_conn',
            'MAIN.backend_unhealthy',
            'MAIN.backend_fail',
            'MAIN.backend_toolate',
            'MAIN.threads_created',
            'MAIN.threads_destroyed',
            'MAIN.threads_failed',
            'MGT.child_start',
            'MGT.child_exit',
            'MGT.child_stop',
            'MGT.child_died',
            'MGT.child_dump',
            'MGT.child_panic'
        ]

        gauge_data = [
            'MAIN.threads',
            'MAIN.threads_limited',
            'MAIN.thread_queue_len'
        ]

        tmp_counter = {}
        for idx in counter_data:
            try:
                tmp_counter[idx] = int(data.get(idx, 0))
            except:
                tmp_counter[idx] = data.get(idx, 0)

        tmp_counter = self.counters(tmp_counter, 'varnish')

        tmp_gauge = {}
        for idx in gauge_data:
            try:
                tmp_gauge[idx] = int(data.get(idx, 0))
            except:
                tmp_gauge[idx] = data.get(idx, 0)

        data = tmp_counter.copy()
        data.update(tmp_gauge)

        metrics = {
            'session stats': {
                'connection': data['MAIN.sess_conn'],
                'drop': data['MAIN.sess_drop'],
                'fail': data['MAIN.sess_fail'],
            },
            'cache stats': {
                'hits': data['MAIN.cache_hit'],
                'misses': data['MAIN.cache_miss']
            },
            'backend connection stats': {
                'success': data['MAIN.backend_conn'],
                'not attempted': data['MAIN.backend_unhealthy'],
                'failures': data['MAIN.backend_fail'],
                'closed': data['MAIN.backend_toolate']
            },
            'thread stats': {
                'threads': data['MAIN.threads'],
                'hit max': data['MAIN.threads_limited'],
                'created': data['MAIN.threads_created'],
                'destroyed': data['MAIN.threads_destroyed'],
                'creation failed': data['MAIN.threads_failed'],
                'session queue': data['MAIN.thread_queue_len']
            },
            'child processes stat': {
                'started': data['MGT.child_start'],
                'normal exit': data['MGT.child_exit'],
                'unexpected exit': data['MGT.child_stop'],
                'died (signal)': data['MGT.child_died'],
                'core dumped': data['MGT.child_dump'],
                'panic': data['MGT.child_panic']
            }
        }

        self.exit(OK, data, metrics)

    def _parse_data(self, raw):
        parsed = {}
        decoded = self._from_json(raw)
        for key in decoded.keys():
            if key == 'timestamp':
                pass
            else:
                parsed[key] = int(decoded[key]['value'])

        return parsed

if __name__ == '__main__':
    monitor = VarnishStatus()
    monitor.run()
