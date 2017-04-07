#!/usr/bin/env python

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'plugins'))

from __mplugin import MPlugin
from __mplugin import OK, CRITICAL, TIMEOUT

class PostfixQueue(MPlugin):

    def get_stats(self):
        # directory - the value of postconf -h queue_directory
        # queues - the postfix mail queues you would like to get message count totals for
        directory = self.config.get('directory', '/var/spool/postfix')
        queue_name = ['active', 'incoming', 'deferred']

        data = {}

        for queue in queue_name:
            try:
                queue_path = os.path.join(directory, queue)
                if not os.path.isdir(queue_path):
                    raise Exception('directory - the value of postconf -h queue_directory')
                count = os.popen('sudo find %s -type f | wc -l' % queue_path)
                data[queue] = int(count.readlines()[0].strip())
            except Exception as e:
                self.exit(CRITICAL, message=str(e))

        return data

    def run(self):
        data = self.get_stats()

        metrics = {
            'Active Queue Length': {
                'Active': data['active'],
            },
            'Incoming Queue Length':{
                'Incoming': data['incoming'],
            },
            'Deffered Queue Length':{
                'Deffered': data['deferred']
            },
        }
        self.exit(OK, data, metrics)

if __name__ == '__main__':
    monitor = PostfixQueue()
    monitor.run()
    