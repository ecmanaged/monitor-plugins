#!/usr/bin/env python

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'plugins'))

from __mplugin import MPlugin
from __mplugin import OK, CRITICAL, TIMEOUT

# Replication states
"""
MongoDB replica set states, as documented at
https://docs.mongodb.org/manual/reference/replica-states/
"""
REPLSET_MEMBER_STATES = {
    0: ('STARTUP', 'Starting Up'),
    1: ('PRIMARY', 'Primary'),
    2: ('SECONDARY', 'Secondary'),
    3: ('RECOVERING', 'Recovering'),
    4: ('Fatal', 'Fatal'),   # MongoDB docs don't list this state
    5: ('STARTUP2', 'Starting up (forking threads)'),
    6: ('UNKNOWN', 'Unknown to this replset member'),
    7: ('ARBITER', 'Arbiter'),
    8: ('DOWN', 'Down'),
    9: ('ROLLBACK', 'Rollback'),
    10: ('REMOVED', 'Removed'),
}


# pip install pymongo
import_error = False
try:
    from pymongo import MongoClient as Client
    from pymongo.errors import ConnectionFailure, AutoReconnect
except:
    import_error = True


class MongoDBReplicaSetStatus(MPlugin):
    def get_stats(self):
        host = self.config.get('hostname', 'localhost')
        port = int(self.config.get('port', '27017'))
        username = self.config.get('user', None)
        password = self.config.get('password', None)

        try:
            if username and password:
                uri = "mongodb://{}:{}@{}:{}".format(username,
                                                     password,
                                                     host,
                                                     port)
                cli = Client(uri)
                admin_db = cli['admin']
                admin_db.authenticate(username, password)
                return admin_db.command("replSetGetStatus")

            else:
                cli = Client(host, port)
                admin_db = cli['admin']
                return admin_db.command("replSetGetStatus")

        except (ConnectionFailure, AutoReconnect):
            self.exit(CRITICAL, message="unable to connect to mongodb")

    def get_state_name(self, state):
        if state in self.REPLSET_MEMBER_STATES:
            return self.REPLSET_MEMBER_STATES[state][0]
        else:
            return 'UNKNOWN'

    def run(self):
        if import_error:
            self.exit(CRITICAL, message="Please install pymongo")

        replSet = self.get_stats()

        message = ''
        status = OK
        data = {}
        metrics = {}

        primary = None
        current = None

        members = replSet.get('members')

        for member in members:
            if member.get('self'):
                current = member
            if int(member.get('state')) == 1:
                primary = member

        if not current:
            self.exit(CRITICAL, message="current replica not found")

        if not primary:
            self.exit(CRITICAL, message="primary replica not found")

        name = current['name']
        state = current['state']

        if state not in [1, 2]:
            status = CRITICAL
            message = "{} is in {}".format(name, status)

        lag = primary['optimeDate'] - current['optimeDate']
        data['replicationLag'] = lag.total_seconds()

        metrics = {
            'Replication Lag': {
                'Seconds': data['replicationLag']
            }
        }

        self.exit(status, data=data, metrics=metrics, message=message)

if __name__ == '__main__':
    monitor = MongoDBReplicaSetStatus()
    monitor.run()
