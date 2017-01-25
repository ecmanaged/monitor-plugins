#!/usr/bin/env python

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'plugins'))

from __mplugin import MPlugin
from __mplugin import OK, CRITICAL

docker_py_error = False
try:
    import requests_unixsocket
    import json
except:
    docker_py_error = True


class CheckDocker(MPlugin):
    def get_stats(self, base_url, container_name):
        base = "http+unix://%2Fvar%2Frun%2Fdocker.sock"
        url = "/containers/json"

        session = requests_unixsocket.Session()
        try:
            resp = session.get(base + url)
            respj = resp.json()
        except Exception as e:
            self.exit(
                CRITICAL,
                message="Run 'sudo usermod -a -G docker ecmanaged' and restart the agent"
                )

        container_id = None
        statj = None

        for container in respj:
            try:
                for name in container['Names']:
                    if container_name == name.split('/')[-1] and container['Status'].startswith('Up'):
                        container_id = container['Id']
            except KeyError:
                if container['name'] == container_name and container['Status'].startswith('Up'):
                    container_id = container['Id']

        if container_id:
            stat_url = "/containers/%s/stats?stream=0" % container_id
            stat = session.get(base + stat_url)
            statj = stat.json()

        return statj

    def run(self):
        if docker_py_error:
            self.exit(CRITICAL, message="please install requests_unixsocket")

        base_url = self.config.get('base_url')
        container_name = self.config.get('container_name')

        stat = self.get_stats(base_url, container_name)

        if not stat:
            self.exit(CRITICAL, message="No container found with name: %s" %container_name)

        data = {}
        counter_data = [
            'read',
            'write',
            'sync',
            'async',
            'network_tx_bytes',
            'network_rx_bytes'
        ]

        gauge_data = [
            'cpu_percent',
            'mem_percent'
        ]

        mem_percent = 0
        cpu_percent = 0

        if stat['memory_stats']['limit'] != 0:
            mem_percent = float(stat['memory_stats']['usage']) / float(stat['memory_stats']['limit']) * 100.0
        data['mem_percent'] = mem_percent

        previousCPU = stat['precpu_stats']['cpu_usage']['total_usage']
        previousSystem = stat['precpu_stats']['system_cpu_usage']

        cpuDelta = stat['cpu_stats']['cpu_usage']['total_usage'] - previousCPU
        systemDelta = stat['cpu_stats']['system_cpu_usage'] - previousSystem

        if systemDelta > 0 and cpuDelta > 0:
            cpu_percent = (float(cpuDelta) / float(systemDelta)) * float(len(stat['cpu_stats']['cpu_usage']['percpu_usage'])) * 100.0
        data['cpu_percent'] = cpu_percent

        try:
            data['network'] = stat['networks']['eth0']
        except KeyError:
            data['network'] = stat['network']

        data['read'] = 0
        data['write'] = 0
        data['sync'] = 0
        data['async'] = 0

        for io in stat['blkio_stats']['io_service_bytes_recursive']:
            if io['op'] == 'Read':
                data['read'] = io['value']
            if io['op'] == 'Write':
                data['write'] = io['value']
            if io['op'] == 'Sync':
                data['sync'] = io['value']
            if io['op'] == 'Async':
                data['async'] = io['value']

        data['network_tx_bytes'] = data['network']['tx_bytes']
        data['network_rx_bytes'] = data['network']['rx_bytes']

        tmp_counter = {}
        for idx in counter_data:
            try:
                tmp_counter[idx] = int(data.get(idx, 0))
            except:
                tmp_counter[idx] = data.get(idx, 0)

        tmp_counter = self.counters(tmp_counter, 'docker')

        tmp_gauge = {}
        for idx in gauge_data:
            try:
                tmp_gauge[idx] = int(data.get(idx, 0))
            except:
                tmp_gauge[idx] = data.get(idx, 0)

        data = tmp_counter.copy()
        data.update(tmp_gauge)

        metrics = {
            'CPU and Memory usage': {
                'CPU percentage': data['cpu_percent'],
                'Memory percentage': data['mem_percent']
            },
            'Network Usage': {
                'Transmitted Bytes': data['network_tx_bytes'],
                'Recieved Bytes': data['network_rx_bytes']
            },
            'Block I/O': {
                'Read': data['read'],
                'Write': data['write'],
                'Sync': data['sync'],
                'Async': data['async']
            }

        }
        self.exit(OK, data, metrics)

if __name__ == '__main__':
    monitor = CheckDocker()
    monitor.run()
