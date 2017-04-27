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

class CheckRedis(MPlugin):

    def get_stats(self):

        if redis_py_error:
            self.exit(CRITICAL, message="please install redis python library (pip install redis)")

        hostname = self.config.get('hostname', 'localhost')
        port = self.config.get('port', '6379')
        password = self.config.get('password', '')

        r = None

        try:
            r = redis.Redis(host=hostname, port=int(port), db=0, password=password)
        except:
            self.exit(CRITICAL, message="could not connect to redis")

        redis_info = None

        try:
            redis_info = r.info()
        except:
            self.exit(CRITICAL, message="can not obtain info")


        if not redis_info:
            self.exit(CRITICAL, message="can not obtain info")

        return redis_info

    def run(self):
        stat = self.get_stats()

        data = {}

        stat_dict = {
            'blocked_clients': 0,
            'connected_clients': 0,
            'connected_slaves': 0,

            'evicted_keys': 0,

            'instantaneous_ops_per_sec': 0,

            'keyspace_hits': 0,
            'keyspace_misses': 0,

            'used_cpu_sys': 0,
            'used_cpu_user': 0,

            'used_memory': 0,
            'used_memory_rss': 0
        }

        for key in stat_dict.keys():
            data[key] = stat[key]
        metrics = {
            'Connections': {
                'Connected Clients': data['connected_clients'],
                'Connected Slaves': data['connected_slaves'],
                'Blocked Clients': data['blocked_clients']
            },
            'Keyspace': {
                'Keyspace hits':data['keyspace_hits'],
                'keyspace misses': data['keyspace_misses'],
                'Evicted Keys': data['evicted_keys']
            },
            'Operation per second': {
                'Ops per sec': data['instantaneous_ops_per_sec']
            },
            'CPU uses': {
                'CPU System': data['used_cpu_sys'],
                'CPU User': data['used_cpu_user']
            },
            'Memory uses': {
                'used memory': data['used_memory']/ (1024 * 1204),
                'used memory rss': data['used_memory_rss']/ (1024 * 1204)
            }

        }
        self.exit(OK, data, metrics)

if __name__ == '__main__':
    monitor = CheckRedis()
    monitor.run()
    
