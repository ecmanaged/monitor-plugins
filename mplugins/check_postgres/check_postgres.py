#!/usr/bin/env python

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'plugins'))

from __mplugin import MPlugin
from __mplugin import OK, CRITICAL, TIMEOUT

import_error = False
try:
    import psycopg2 as pg
except:
    import_error = True

class PostGresCheck(MPlugin):
    DB_METRICS = {
        'descriptors': [('datname', 'db')],
        'metrics': {'numbackends': 'connections',
                    'xact_commit': 'commits',
                    'xact_rollback': 'rollbacks',
                    'blks_read': 'disk_read',
                    'blks_hit': 'buffer_hit',
                    'tup_returned': 'rows_returned',
                    'tup_fetched': 'rows_fetched',
                    'tup_inserted': 'rows_inserted',
                    'tup_updated': 'rows_updated',
                    'tup_deleted': 'rows_deleted'},
        'query': """
SELECT datname,
       %s
  FROM pg_stat_database
 WHERE datname not ilike 'template%%'
   AND datname not ilike 'postgres'
""",
        'relation': False,
    }

    NEWER_92_METRICS = {
        'deadlocks': 'deadlocks',
        'temp_bytes': 'temp_bytes',
        'temp_files': 'temp_files',
    }

    REL_METRICS = {
        'descriptors': [('relname', 'table')],
        'metrics': {'seq_scan': 'seq_scans',
                    'seq_tup_read': 'seq_rows_read',
                    'idx_scan': 'index_scans',
                    'idx_tup_fetch': 'index_rows_fetched',
                    'n_tup_ins': 'rows_inserted',
                    'n_tup_upd': 'rows_updated',
                    'n_tup_del': 'rows_deleted',
                    'n_tup_hot_upd': 'rows_hot_updated',
                    'n_live_tup': 'live_rows',
                    'n_dead_tup': 'dead_rows'},
        'query': """
SELECT relname,
       %s
  FROM pg_stat_user_tables
 WHERE relname = ANY(%s)""",
        'relation': True,
    }

    IDX_METRICS = {
        'descriptors': [
            ('relname', 'table'),
            ('indexrelname', 'index')
        ],
        'metrics': {
            'idx_scan': 'index_scans',
            'idx_tup_read': 'index_rows_read',
            'idx_tup_fetch': 'index_rows_fetched',
        },
        'query': """
SELECT relname,
       indexrelname,
       %s
  FROM pg_stat_user_indexes
 WHERE relname = ANY(%s)""",
        'relation': True,
    }

    @staticmethod
    def get_library_versions():
        try:
            import psycopg2
            version = psycopg2.__version__
        except ImportError:
            version = "Not Found"
        except AttributeError:
            version = "Unknown"
        return {"psycopg2": version}

    def _get_version(self, db):
        cursor = db.cursor()
        cursor.execute('SHOW SERVER_VERSION;')
        result = cursor.fetchone()
        try:
            version = map(int, result[0].split('.'))
        except Exception:
            version = result[0]
        return version

    def _is_9_2_or_above(self, db):
        version = self._get_version(db)
        if isinstance(version, list):
            return version >= [9, 2, 0]
        return False

    def _collect_stats(self, db, relations):
        """Query pg_stat_* for various metrics

        If relations is not an empty list, gather per-relation metrics
        on top of that.
        """
        # Extended 9.2+ metrics
        if self._is_9_2_or_above(db):
            self.DB_METRICS['metrics'].update(self.NEWER_92_METRICS)

        # Do we need relation-specific metrics?
        if not relations:
            metric_scope = (self.DB_METRICS,)
        else:
            metric_scope = (self.DB_METRICS, self.REL_METRICS, self.IDX_METRICS)

        for scope in metric_scope:
            # build query
            cols = scope['metrics'].keys()  # list of metrics to query, in some order
            # we must remember that order to parse results
            try:
                cursor = db.cursor()
            except Exception as e:
                self.exit(CRITICAL, message="Connection seems broken: %s" % str(e))


            # if this is a relation-specific query, we need to list all relations last
            if scope['relation'] and len(relations) > 0:
                query = scope['query'] % (", ".join(cols), "%s")  # Keep the last %s intact
                cursor.execute(query, (relations, ))
            else:
                query = scope['query'] % (", ".join(cols))
                cursor.execute(query)

            results = cursor.fetchall()
            cursor.close()

            for row in results:
                desc = scope['descriptors']

                dbname = row[0]
                self.data[dbname] = {}

                values = zip([scope['metrics'][c] for c in cols], row[len(desc):])

                for key, value in values:
                    self.data[dbname][key] = value


    def get_connection(self, host, port, user, password, dbname):
        """Get and memorize connections to instances.

        """
        if host != "" and user != "":
            if port != '':
                connection = pg.connect(host=host, port=port, user=user,
                                        password=password, database=dbname)
            else:
                connection = pg.connect(host=host, user=user, password=password,
                                        database=dbname)
        else:
            if not host:
                self.exit(CRITICAL, message="Please specify a Postgres host to connect to.")
            elif not user:
                self.exit(CRITICAL, message="Please specify a user to connect to Postgres as.")

        try:
            connection.autocommit = True
        except AttributeError:
            # connection.autocommit was added in version 2.4.2
            from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
            connection.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)

        return connection

    def run(self):
        if import_error:
            self.exit(CRITICAL, message="psycopg2 library cannot be imported.")

        host = self.config.get('host', '')
        port = self.config.get('port', '')
        user = self.config.get('username', '')
        password = self.config.get('password', '')
        dbname = self.config.get('dbname', 'postgres')
        relations = self.config.get('relations', [])

        self.data = {}

        if relations:
            relations = relations.split(',')

        key = '%s:%s:%s' % (host, port, dbname)
        db = self.get_connection(host, port, user, password, dbname)

        version = self._get_version(db)

        try:
            self._collect_stats(db, relations)
        except Exception:
            self.exit(CRITICAL, message="failed to obtain metrics")

        counter_data = [
            'commits',
            'rollbacks',
            'disk_read',
            'buffer_hit',
            'rows_deleted',
            'temp_bytes',
            'temp_files',
            'rows_returned',
            'rows_fetched',
            'rows_inserted',
            'rows_updated',
        ]

        gauge_data = [
            'connections',
            'deadlocks',
        ]

        data_final = {}

        for item in self.data:
            tmp_counter = {}
            for idx in counter_data:
                try:
                    tmp_counter[idx] = int(self.data[item].get(idx, 0))
                except:
                    tmp_counter[idx] = self.data[item].get(idx, 0)

            tmp_counter = self.counters(tmp_counter, item)

            tmp_gauge = {}
            for idx in gauge_data:
                try:
                    tmp_gauge[idx] = int(self.data[item].get(idx, 0))
                except:
                    tmp_gauge[idx] = self.data[item].get(idx, 0)

            data_temp = tmp_counter.copy()
            data_temp.update(tmp_gauge)

            data_final[item] = data_temp

        metrics = {}

        for item in data_final:
            metrics_tmp = {
                'Connections on {}'.format(item): {
                    'connections': data_final[item]['connections']
                },

                'Deadlocks on {}'.format(item): {
                    'connections': data_final[item]['deadlocks']
                },

                'Row statistics on {}'.format(item): {
                    'rows returned': data_final[item]['rows_returned'],
                    'rows fetched': data_final[item]['rows_fetched'],
                    'rows inserted': data_final[item]['rows_inserted'],
                    'rows updated': data_final[item]['rows_updated'],
                    'rows deleted': data_final[item]['rows_deleted'],

                },
                'Commits and rollbacks on {}'.format(item): {
                    'commits': data_final[item]['commits'],
                    'rollbacks': data_final[item]['rollbacks'],
                },

                ' IO statistics on {}'.format(item): {
                    'disk_read': data_final[item]['disk_read'],
                    'buffer_hit': data_final[item]['buffer_hit'],
                    'rows_deleted': data_final[item]['rows_deleted'],
                    'temp_bytes': data_final[item]['temp_bytes'],
                    'temp_files': data_final[item]['temp_files'],
                },
            }
            metrics.update(metrics_tmp)

        self.exit(OK, data_final, metrics)


if __name__ == '__main__':
    monitor = PostGresCheck()
    monitor.run()