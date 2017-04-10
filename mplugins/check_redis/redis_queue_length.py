#!/usr/bin/env python

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'plugins'))

from __mplugin import MPlugin
from __mplugin import OK, CRITICAL, TIMEOUT

redis_py_error = False
try:
    import redis
except:
    redis_py_error = True

class RedisQueueLength(MPlugin):

    def get_stats(self):

        if redis_py_error:
            self.exit(CRITICAL, message="please install redis python library (pip install redis)")

        hostname = self.config.get('hostname', 'localhost')
        port = self.config.get('port', '6379')
        password = self.config.get('password', '')
        queue_name = self.config.get('queue_name')

        r = None

        try:
            r = redis.Redis(host=hostname, port=int(port), db=0, password=password)
        except:
            self.exit(CRITICAL, message="could not connect to redis")

        queue_length = None

        try:
            queue_length = r.llen(queue_name)
        except:
            self.exit(CRITICAL, message="can not obtain queue length")

        if not queue_length:
            self.exit(CRITICAL, message="can not obtain queue length")

        return {'length': queue_length}

    def run(self):
        data = self.get_stats()

        metrics = {
            'redis_queue': data['length']
        }
        self.exit(OK, data, metrics)

if __name__ == '__main__':
    monitor = RedisQueueLength()
    monitor.run()
