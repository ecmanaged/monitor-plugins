#!/usr/bin/env python

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'plugins'))

from __mplugin import MPlugin
from __mplugin import OK, CRITICAL, TIMEOUT


# pip install python-memcached
import_error = False
try:
    import memcache
except:
    import_error = True


class MemcacheStatus(MPlugin):

    def get_stats(self):
        host = self.config.get('host')
        port = self.config.get('port')

        if import_error:
            self.exit(CRITICAL, message="Please install python-memcached")
        
        memcache_client = memcache.Client(['%s:%s' %(host,port)])
        memcache_stats = memcache_client.get_stats()
        
        if not memcache_stats:
            self.exit(CRITICAL, message="Unable to connect to memcache %s:%s" %(host,port))
            
        return memcache_stats[0][1]

    def run(self):
        data = self.get_stats()
        
        counter_data = [
           'cmd_get',
           'cmd_set',
           'cmd_flush',
           'cmd_touch',
           
           'total_connections',
           
           'get_hits',
           'get_misses',
           
           'delete_misses',
           'delete_hits',
           
           'incr_misses',
           'incr_hits',
           
           'decr_misses',
           'decr_hits',
           
           'cas_misses',
           'cas_hits',
           'cas_badval',
           
           'cas_misses',
           'cas_hits',
           'cas_badval',
           
           'touch_hits',
           'touch_misses',
           
           'auth_cmds',
           'auth_errors',
           
           'evictions',
           
           'reclaimed',
           
           'bytes_read',
           'bytes_written',
           
           'conn_yields'           
        ]
        
        gauge_data = [
            'rusage_user',
            'rusage_system',
            
            'curr_items',
            'total_items',
            'bytes',
            
            'curr_connections',
            
            'threads'            
        ]
        
        tmp_counter = {}
        for idx in counter_data:
            try:
                tmp_counter[idx] = int(data.get(idx,0))
            except:
                tmp_counter[idx] = data.get(idx,0)
        
        tmp_counter = self.counters(tmp_counter,'memcache')
      
        tmp_gauge = {}
        for idx in gauge_data:
            try:
                tmp_gauge[idx] = int(data.get(idx,0))
            except:
                tmp_gauge[idx] = data.get(idx,0)
                        
        data = tmp_counter.copy()
        data.update(tmp_gauge)
        
        get_hits = int(data['get_hits'])
        get_misses = int(data['get_misses'])
        try:
            data['hit_percentage'] = (get_hits/(get_hits+get_misses)) * 100
            data['miss_percentage'] = (get_misses/(get_hits+get_misses)) * 100
        except:
            data['hit_percentage'] = 0
            data['miss_percentage'] = 0
        
        metrics = {
                    'usage': {
                                'user time' : data['rusage_user'],
                                'system time' : data['rusage_system']
                    },
                    'requests': {
                                'retrieval reqs' : data['cmd_get'],
                                'storage reqs' : data['cmd_set'],
                                'flush reqs' : data['cmd_flush'],
                                'touch reqs' : data['cmd_touch']
                    },
                    'items': {
                            'current number of items stored' : data['curr_items'],
                            'number of items stored' : data['total_items'],
                            'bytes used to store items' : data['bytes']
                    },
                    'connections': {
                            'open connections' : data['curr_connections'],
                            'number of connections' : data['total_connections']
                    },
                    'hits and misses':{
                            'items found' : data['get_hits'],
                            'items not found' : data['get_misses']
                    },
                    'deletions':{
                            'deletions reqs for missing keys' : data['delete_misses'],
                            'deletion reqs' : data['delete_hits']
                    },
                    'increments':{
                            'incr reqs against missing keys.' : data['incr_misses'],
                            'successful incr reqs' : data['incr_hits']
                    },
                    'decrements':{
                            'decr reqs against missing keys' : data['decr_misses'],
                            'successful decr reqs' : data['decr_hits']
                    },
                    'check and set':{
                            'CAS reqs against missing keys' : data['cas_misses'],
                            'successful CAS reqs' : data['cas_hits'],
                            'mismatched CAS reqs ' : data['cas_badval']
                    },
                    'touch':{
                            'touched with a new expiration time' : data['touch_hits'],
                            'touched and not found' : data['touch_misses']
                    },
                    'authentication commands':{
                            'authentication commands handled' : data['auth_cmds'],
                            'Number of failed authentications' : data['auth_errors']
                    },
                    'evictions':{
                            'number of evicted items' : data['evictions']
                    },
                    'reclaimed':{
                            'number of reclaimed items' : data['reclaimed']
                    },
                    'network':{
                            'bytes read from network' : data['bytes_read'],
                            'bytes sent by to network' : data['bytes_written']
                    },
                    'worker thread':{
                            'worker threads requested' : data['threads']
                    },
                    'yielded connections':{
                            'yielded connections' : data['conn_yields']
                    }
                 }
        self.exit(OK, data, metrics)    
                  
if __name__ == '__main__':    
    monitor = MemcacheStatus()
    monitor.run()