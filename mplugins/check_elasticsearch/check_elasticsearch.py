#!/usr/bin/env python

import urllib2
import json

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'plugins'))

from __mplugin import MPlugin
from __mplugin import OK, CRITICAL


class ElasticSearchStatus(MPlugin):
    def call_to_cluster(self, host, path):
        """Call a given path to the cluster and return JSON."""

        try:
            r = urllib2.urlopen('{h}{p}'.format(h=host, p=path))
        except (urllib2.URLError, ValueError):
            self.exit(CRITICAL, message='error opening url')

        try:
            response = json.loads(r.read())
        except Exception:
            self.exit(CRITICAL, message='error loading json')

        return response

    def get_stats(self, host, keyname):
        """Return a dict of stats from /_cluster/nodes/_local/stats.
        Keyname can be one of: docs, search, indexing, store, get"""

        h = self.call_to_cluster(host, '/_nodes/stats')

        node_name = h['nodes'].keys()[0]
        stats = h['nodes'][node_name]['indices'][keyname]

        return stats

    def cluster_health(self, host):
        """Return metrics about /_cluster/health."""

        h = self.call_to_cluster(host, '/_cluster/health')

        data = {
            'number_of_nodes': h['number_of_nodes'],
            'unassigned_shards': h['unassigned_shards'],
            'timed_out': h['timed_out'],
            'active_primary_shards': h['active_primary_shards'],
            'relocating_shards': h['relocating_shards'],
            'active_shards': h['active_shards'],
            'initializing_shards': h['initializing_shards'],
            'number_of_data_nodes': h['number_of_data_nodes']
            }

        return data

    def stats_store(self, host):
        """Return store metrics from /_cluster/nodes/_local/stats."""

        s = self.get_stats(host, 'store')

        data = {
            'size_in_bytes': s['size_in_bytes'],
            'throttle_time_in_millis': s['throttle_time_in_millis']
            }

        return data

    def stats_indexing(self, host):
        """Return indexing metrics from /_cluster/nodes/_local/stats."""

        s = self.get_stats(host, 'indexing')

        data = {
            'delete_time_in_millis': s['delete_time_in_millis'],
            'delete_total': s['delete_total'],
            'delete_current': s['delete_current'],
            'index_time_in_millis': s['index_time_in_millis'],
            'index_total': s['index_total'],
            'index_current': s['index_current']
            }

        return data

    def stats_get(self, host):
        """Return GET metrics from /_cluster/nodes/_local/stats."""

        s = self.get_stats(host, 'get')

        data = {
            'missing_total': s['missing_total'],
            'exists_total': s['exists_total'],
            'current': s['current'],
            'total': s['total']
            }

        return data

    def stats_search(self, host):
        """Return search metrics from /_cluster/nodes/_local/stats."""

        s = self.get_stats(host, 'search')

        data = {
            'query_total': s['query_total'],
            'fetch_time_in_millis': s['query_time_in_millis'],
            'fetch_total': s['fetch_total'],
            'query_time_in_millis': s['fetch_time_in_millis'],
            'open_contexts': s['open_contexts'],
            'fetch_current': s['fetch_current'],
            'query_current': s['query_current']
            }

        return data

    def stats_docs(self, host):
        """Return doc metrics from /_cluster/nodes/_local/stats."""

        s = self.get_stats(host, 'docs')

        data = {
            'count': s['count'],
            'deleted': s['deleted']
            }

        return data

    def run(self):
        host = self.config.get('hostname', 'http://localhost:9200')

        data = self.cluster_health(host)
        data.update(self.stats_store(host))
        data.update(self.stats_indexing(host))
        data.update(self.stats_get(host))
        data.update(self.stats_search(host))
        data.update(self.stats_docs(host))

        metrics = {
            'Cluster Health': {
                'number of nodes': data['number_of_nodes'],
                'unassigned shards': data['unassigned_shards'],
                'timed out': data['timed_out'],
                'active primary shards': data['active_primary_shards'],
                'relocating shards': data['relocating_shards'],
                'active shards': data['active_shards'],
                'initializing shards': data['initializing_shards'],
                'number of data nodes': data['number_of_data_nodes']
            },
            'Store Statistics': {
                'size in bytes': data['size_in_bytes'],
                'throttle time in millis': data['throttle_time_in_millis']
            },
            'Indexing Statistics': {
                'delete time in millis': data['delete_time_in_millis'],
                'delete total': data['delete_total'],
                'delete current': data['delete_current'],
                'index time in millis': data['index_time_in_millis'],
                'index total': data['index_total'],
                'index current': data['index_current']
            },
            'GET Statistics': {
                'missing total': data['missing_total'],
                'exists total': data['exists_total'],
                'current': data['current'],
                'total': data['total']
            },
            'Search Statistics': {
                'query_total': data['query_total'],
                'fetch_time_in_millis': data['query_time_in_millis'],
                'fetch_total': data['fetch_total'],
                'query_time_in_millis': data['fetch_time_in_millis'],
                'open_contexts': data['open_contexts'],
                'fetch_current': data['fetch_current'],
                'query_current': data['query_current']
            },
            'Doc Statistics': {
                'count': data['count'],
                'deleted': data['deleted']
            }
        }
        self.exit(OK, data, metrics)

if __name__ == '__main__':
    monitor = ElasticSearchStatus()
    monitor.run()

    