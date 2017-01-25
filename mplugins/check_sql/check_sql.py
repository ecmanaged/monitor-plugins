#!/usr/bin/env python

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'plugins'))

from __mplugin import MPlugin
from __mplugin import OK, CRITICAL

adodbapi_import_error = False
try:
    import adodbapi
except:
    adodbapi_import_error = True

ALL_INSTANCES = 'ALL'

class CheckIIS(MPlugin):
    def get_stats(self):
        host = self.config.get('hostname', 'localhost')
        database = self.config.get('database')
        # GRANT VIEW SERVER STATE TO username
        username = self.config.get('username')
        password = self.config.get('password')
        conn_str = self._conn_string(host, username, password, database)

        try:
            conn = adodbapi.connect(conn_str)
        except Exception:
            self.exit(CRITICAL, message="Unable to connect to SQL Server for instance")

        cursor = conn.cursor()

        stats = {}

        METRICS = [
            ('sqlserver.buffer.cache_hit_ratio', 'gauge', 'Buffer cache hit ratio'),
            ('sqlserver.buffer.page_life_expectancy', 'gauge', 'Page life expectancy'),
            ('sqlserver.stats.batch_requests', 'gauge', 'Batch Requests/sec'),
            ('sqlserver.stats.sql_compilations', 'gauge', 'SQL Compilations/sec'),
            ('sqlserver.stats.sql_recompilations', 'gauge', 'SQL Re-Compilations/sec'),
            ('sqlserver.stats.connections', 'gauge', 'User connections'),
            ('sqlserver.stats.lock_waits', 'gauge', 'Lock Waits/sec', '_Total'),
            ('sqlserver.access.page_splits', 'gauge', 'Page Splits/sec'),
            ('sqlserver.stats.procs_blocked', 'gauge', 'Processes Blocked'),
            ('sqlserver.buffer.checkpoint_pages', 'gauge', 'Checkpoint pages/sec')
        ]

        for metric in METRICS:
            # Normalize all rows to the same size for easy of use
            if len(metric) == 3:
                metric = metric + ('', None)
            elif len(metric) == 4:
                metric = metric + (None,)

            mname, mtype, counter, instance_n, tag_by = metric

            # For "ALL" instances, we run a separate method because we have
            # to loop over multiple results and tag the metrics
            try:
                cursor.execute("""
                    select cntr_value
                    from sys.dm_os_performance_counters
                    where counter_name = ?
                    and instance_name = ?
                 """, (counter, instance_n))
                (value,) = cursor.fetchone()
                stats[counter] = value
            except Exception:
                stats[counter] = 0

        return stats

    def run(self):
        if adodbapi_import_error:
            self.exit(CRITICAL, message="please install adodbapi(pip install adodbapi)")

        data = self.get_stats()
        if not data:
            self.exit(CRITICAL, message="Unable fetch stats")

        metrics = {
            'Buffer Manager': {
                'Buffer cache hit ratio': data['Buffer cache hit ratio'],
                'Page life expectancy': data['Page life expectancy']
            },
            'Checkpoint Pages': {
                'Checkpoint pages/sec': data['Checkpoint pages/sec']

            },
            'SQL Statistics': {
                'SQL Compilations/sec': data['SQL Compilations/sec'],
                'SQL Re-Compilations/sec': data['SQL Re-Compilations/sec']
            },
            'Batch Requests': {
                'Batch Requests/sec': data['Batch Requests/sec'],
            },
            'General Statistics': {
                'User connections': data['User connections']
            },
            'Locks': {
                'Lock Waits/sec': data['Lock Waits/sec']
            },
            'Access Methods': {
                'Page Splits/sec': data['Page Splits/sec']
            },
            'General Statistic': {
                'Processes Blocked': data['Processes Blocked']
            },
        }
        self.exit(OK, data, metrics)


    @staticmethod
    def _conn_string(host, username, password, database):
        """Return a connection string to use with adodbapi.
        """
        conn_str = 'Provider=SQLOLEDB;Data Source=%s;Initial Catalog=%s;' % (host, database)
        if username:
            conn_str += 'User ID=%s;' % (username)
        if password:
            conn_str += 'Password=%s;' % (password)
        if not username and not password:
            conn_str += 'Integrated Security=SSPI;'
        return conn_str

if __name__ == '__main__':
    monitor = CheckIIS()
    monitor.run()
    