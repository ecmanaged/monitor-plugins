#!/usr/bin/env python

import sys
import os
import math

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'plugins'))

from __mplugin import MPlugin
from __mplugin import OK, CRITICAL, TIMEOUT

import requests

NODE_CONDITIONS_MAP = {
    "OutOfDisk": {
        "metric_name": "node.out_of_disk",
        "expected_status": "False"
    },
    "MemoryPressure": {
        "metric_name": "node.memory_pressure",
        "expected_status": "False"
    },
    "DiskPressure": {
        "metric_name": "node.disk_pressure",
        "expected_status": "False"
    },
    "Ready": {
        "metric_name": "node.ready_status",
        "expected_status": "True"
    }
}

class CheckKubernetesAPI(MPlugin):
    def run(self):
        self.kube_api = self.config.get('url')
        self.data = {}
        self.metrics = {}
        self.status = None
        self.message = ''

        try:
            # check kubernetes api health_status
            result = self._send_request("healthz", as_json=False)

            if not result.content == 'ok':
                self.status = CRITICAL
                self.message += 'health_status: Critical'

            self.message = 'health_status: OK'

            # report cluster component statuses
            self._report_cluster_component_statuses()

            #self._report_deployment_metrics()

            self._report_nodes_metrics()

            if not self.status:
                self.status = OK

            self.exit(self.status, data=self.data, metrics=self.metrics, message=self.message)

        except Exception as e:
            self.exit(CRITICAL, message='Error getting data from Kubernetes API')

    def _report_cluster_component_statuses(self):
        component_statuses = self._send_request("/api/v1/componentstatuses")

        for component in component_statuses['items']:
            component_conditions = component['conditions']
            for condition in component_conditions:
                if 'type' in condition and condition['type'] != 'Healthy':
                    self.status = CRITICAL
                    self.message += ', Component {} is {}'.format(
                        component['metadata']['name'],
                        component['metadata']['message'])

                if 'status' in condition and not condition['status']:
                    self.status = CRITICAL
                    self.message += ', Component {} is {}'.format(
                        component['metadata']['name'],
                        component['metadata']['message'])


    def _report_deployment_metrics(self):
        deployments = self._send_request("/apis/extensions/v1beta1/deployments")

        for deployment in deployments['items']:
            deployment_status = deployment['status']
            deployment_replicas = deployment_status['replicas']
            deployment_available_replicas = deployment_status.get('availableReplicas', 0)

            if deployment_replicas != deployment_available_replicas:
                self.status = CRITICAL
                self.message += ', {} on {} has unavailable replicas'.format(
                    deployment['metadata']['name'],
                    deployment['metadata']['namespace'])

    def _report_nodes_metrics(self):
        nodes = self._send_request("/api/v1/nodes")

        self.data['node_count'] = len(nodes['items'])
        self.metrics = {
            'Number of Nodes':{
                'Number of Nodes': self.data['node_count']
            }
        }

        for node in nodes['items']:
            node_name = node['metadata']['name']
            node_status = node['status']
            self._report_node_conditions_metrics(node_name, node_status['conditions'])

    def _report_node_conditions_metrics(self, node_name, node_conditions):
        for condition in node_conditions:
            condition_type = condition["type"]
            if condition_type in NODE_CONDITIONS_MAP:
                condition_map = NODE_CONDITIONS_MAP[condition_type]
                condition_status = condition['status']
                if not condition_status == condition_map['expected_status']:
                    self.status = CRITICAL
                    self.message += ', {}: {} is {}'.format(node_name,
                                                          condition_type,
                                                          condition['reason'])

    def _send_request(self, endpoint, as_json=True):
        result = requests.get("{}/{}".format(self.kube_api, endpoint))
        return result.json() if as_json else result

if __name__ == '__main__':
    MONITOR = CheckKubernetesAPI()
    MONITOR.run()
