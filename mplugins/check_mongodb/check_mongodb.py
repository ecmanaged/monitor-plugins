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
        host = self.config.get('hostname', 'localhost')
        port = int(self.config.get('port', '27017'))
        database = self.config.get('database', None)
        username = self.config.get('user', None)
        password = self.config.get('password', None)

        try:
            if username and password and database:
                uri = "mongodb://{}:{}@{}:{}/{}".format(username,
                                                        password,
                                                        host,
                                                        port,
                                                        database)
                cli = Client(uri)
                check_db = cli[database]
                check_db.authenticate(username, password)
                return check_db.command("serverStatus")

            elif username and password:
                uri = "mongodb://{}:{}@{}:{}".format(username,
                                                     password,
                                                     host,
                                                     port)
                cli = Client(uri)
                return cli.test.command("serverStatus")

            elif database:
                uri = "mongodb://{}:{}/{}".format(host,
                                                  port,
                                                  database)
                cli = Client(uri)
                check_db = cli[database]
                return check_db.command("serverStatus")
            else:
                cli = Client(host, port)
                return cli.test.command("serverStatus")

        except (ConnectionFailure, AutoReconnect):
            self.exit(CRITICAL, message="unable to connect to mongodb")

    def run(self):
        if import_error:
            self.exit(CRITICAL, message="Please install pymongo")

        s = self.get_stats()

        if not s:
            self.exit(CRITICAL, message="status err unable to generate statistics")

        data = {
            'connection_available': s['connections']['available'],
            'connection_current': s['connections']['current'],
            'mem_mapped': s['mem']['mapped'],
            'mem_resident': s['mem']['resident'],
            'mem_virtual': s['mem']['virtual']
        }
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
        }

        self.exit(OK, data, metrics)

if __name__ == '__main__':
    monitor = MongoDBStatus()
    monitor.run()
