#!/usr/bin/env python

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'plugins'))

from __mplugin import MPlugin
from __mplugin import OK, CRITICAL, TIMEOUT


# pip install pymongo
import_error = False
try:
    from pymongo import MongoClient as Client
    from pymongo.errors import ConnectionFailure, AutoReconnect
except:
    import_error = True


class MongoDBStatus(MPlugin):

    def get_stats(self):
        host = self.config.get('hostname','localhost')
        port = int(self.config.get('port','27017'))
        database = self.config.get('database')
        username = self.config.get('username')
        password = self.config.get('password')

        try:
            if username and password and database:
                c = Client("mongodb://"+username+":"+password+"@"+host+"/"+database, port)
            elif username and password:
                c = Client('mongodb://'+username+':'+password+'@'+host+'/', port)
            elif database:
                c = Client('mongodb://'+host+'/'+database, port)
            else:
                c = Client(host, port)
        except ConnectionFailure, AutoReconnect:
            self.exit(CRITICAL, message="unable to connect to mongodb")
        else:
            return c.test.command("serverStatus")




    def run(self):
        if import_error:
            self.exit(CRITICAL, message="Please install pymongo")

        s = self.get_stats()

        if not s:
            self.exit(CRITICAL, message="status err unable to generate statistics")

        data = {'connection_available': s['connections']['available'],
                'connection_current': s['connections']['current'], 'mem_mapped': s['mem']['mapped'],
                'mem_resident': s['mem']['resident'], 'mem_virtual': s['mem']['virtual'],
                'index_hits': s['indexCounters']['hits'], 'index_misses': s['indexCounters']['misses'],
                'index_accesses': s['indexCounters']['accesses']}
        metrics = {
            'Connection': {
                'Current': data['connection_current'],
                'Available': data['connection_available']
            },
            'Memory': {
                'Mapred': data['mem_mapped'],
                'Resident': data['mem_resident'],
                'Virtual': data['mem_virtual']
            },

            'Index': {
                'Hits': data['index_hits'],
                'Misses': data['index_misses'],
                'Accesses': data['index_accesses']
            }
        }

        self.exit(OK, data, metrics)
                  
if __name__ == '__main__':    
    monitor = MongoDBStatus()
    monitor.run()