#!/usr/bin/env python

import re
import subprocess

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'plugins'))

from __mplugin import MPlugin
from __mplugin import OK, CRITICAL

METRIC_TYPES = {
  'list_queues': {
    'name': 'string',
    'durable': 'string',
    'auto_delete': 'string',
    'arguments': 'string',
    'pid': 'int',
    'owner_pid': 'int',
    'messages_ready': 'int',
    'messages_unacknowledged': 'int',
    'messages': 'int',
    'consumers': 'int',
    'memory': 'int'
  },

  'list_exchanges': {
    'name': 'string',
    'type': 'string',
    'durable': 'string',
    'auto_delete': 'string',
    'internal': 'string',
    'argument': 'string'
  }
}


class CheckRabbitMQ(MPlugin):
    def retrieve_stats(self, vhost, action, queue, exchange, parameters, rabbitmqctl_path):
      value = queue or exchange
      command = [ rabbitmqctl_path, action, '-p', vhost ]
      parameters = parameters.split(',')

      parameters = [ p.lower() for p in parameters \
                     if p.lower() in METRIC_TYPES[action].keys() ]

      command.extend( [ 'name' ] + parameters)
      process1 = subprocess.Popen(command, stdout=subprocess.PIPE,
                                 stderr=subprocess.STDOUT)
      process2 = subprocess.Popen([ 'grep', value ], stdin=process1.stdout,
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE)
      process1.stdout.close()
      stdout, stderr = process2.communicate()

      if stderr:
          self.exit(CRITICAL, message=stderr)

      stdout = stdout.split('\n')
      stdout = stdout[0]

      if not stdout:
          self.exit(CRITICAL, message='Empty output')

      return self.parse_stats( [ 'name' ] + parameters, stdout), None

    def parse_stats(self, parameters, data):
      values = re.split('\s+', data)

      stats = {}
      for index, parameter in enumerate(parameters):
        stats[parameter] = values[index]

      return stats

    def run(self):
        rabbitmqctl_path = self.config.get('rabbitmqctl_path')
        action = self.config.get('action')
        vhost = self.config.get('vhost')
        queue = self.config.get('queue')
        exchange = self.config.get('exchange')
        parameters = self.config.get('parameters')

        if not action:
            self.exit(CRITICAL, message='status err Missing required argument: action')

        if action == 'list_queues' and not queue:
            self.exit(CRITICAL, message='status err Missing required argument: queue')

        elif action == 'list_exchanges' and not exchange:
            self.exit(CRITICAL, message='status err Missing required argument: exchange')

        if action not in METRIC_TYPES.keys():
            self.exit(CRITICAL, message='status err Invalid action: %s' % (action))

        if not parameters:
            self.exit(CRITICAL, message='status err Missing required argument: parameters')

        metrics, error = self.retrieve_stats(vhost, action, queue, exchange, parameters, rabbitmqctl_path)

        if error:
            self.exit(CRITICAL, message='status err %s' % (error))

if __name__ == '__main__':
    monitor = CheckRabbitMQ()
    monitor.run()

