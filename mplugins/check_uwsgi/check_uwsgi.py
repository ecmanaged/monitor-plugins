#!/usr/bin/env python

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'plugins'))

from __mplugin import MPlugin
from __mplugin import OK, CRITICAL, TIMEOUT


class UWSGIStatus(MPlugin):

    def get_stats(self):
        from commands import getstatusoutput
        import json

        if not self.which('uwsgi'):
            self.exit(CRITICAL, message="Please install uwsgi")


        host = self.config.get('host')
        port = self.config.get('port')

        retcode, raw_result = getstatusoutput('uwsgi --connect-and-read '+host+":"+port)

        if retcode != 0 or not raw_result:
            self.exit(CRITICAL, message="could not parse data from "+host+":"+port)

        result = json.loads(raw_result)

        return result

    def run(self):
        data = self.get_stats()

        data['idle_worker'] = 0
        data['active_worker'] = 0

        for worker in data['workers']:
            if worker['status'] == 'idle':
                data['idle_worker'] = data['idle_worker'] + 1
            elif worker['status'] == 'active':
                data['active_worker'] = data['active_worker'] + 1

        counter_data = [
            'load',
            'listen_queue',
            'listen_queue_errors',
            'signal_queue',
            'idle_worker',
            'active_worker'
        ]

        tmp_counter = {}
        for idx in counter_data:
            try:
                tmp_counter[idx] = int(data.get(idx, 0))
            except:
                tmp_counter[idx] = data.get(idx, 0)

        tmp_counter = self.counters(tmp_counter, 'uwsgi')


        data = tmp_counter.copy()

        metrics = {
            'Load': {
                'load': data['load']
            },
            'Queue': {
                'listen queue': data['listen_queue'],
                'listen queue errors': data['listen_queue_errors'],
                'signal queue': data['signal_queue']
            },
            'Workers': {
                'active worker': data['active_worker'],
                'idle worker': data['idle_worker']
            }
        }

        self.exit(OK, data, metrics)

if __name__ == '__main__':
    monitor = UWSGIStatus()
    monitor.run()