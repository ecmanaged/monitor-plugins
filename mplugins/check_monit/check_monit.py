#!/usr/bin/env python

# based on monit.py by Camilo Polymeris, 2015
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import urllib2
import base64

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'plugins'))

from __mplugin import MPlugin
from __mplugin import OK, CRITICAL

MIN_METRICS = 3


class Monit(MPlugin):
    def run(self):
        username = self.config.get('username', '')
        password = self.config.get('password', '')
        port = self.config.get('port')

        try:
            mons = MonitConn(username=username, password=password, port=port)
        except Exception as e:
            self.exit(CRITICAL, message=e.message)

        data = {}
        metrics = {}
        msglist = []
        result = OK

        for mon in mons.keys():
            state = mons[mon].running
            enabled = mons[mon].monitored
            kind = mons[mon].type
            name = mons[mon].name
            extra = mons[mon].data

            if not name:
                continue

            if not state:
                result = CRITICAL
                msglist.append("%s %s is critical" % (kind, name))

            if not enabled:
                result = CRITICAL
                msglist.append("%s %s is not monitored" % (kind, name))

            # Custom name
            name = name + ': ' + kind

            # Add data
            data[name] = {
                'kind': kind,
                'state': state,
                'enabled': enabled,
                'data': extra
            }

            # Create metrics
            metrics[name] = {}
            count_metrics = 0

            for k in extra.keys():
                metrics[name][k] = extra[k]
                count_metrics = count_metrics + 1

            # Add placeholder for metrics (each monit has to have the same number of metrics)
            for i in range(count_metrics, MIN_METRICS):
                metrics[name]['__ph__' + str(i)] = ''

        if not msglist:
            msglist.append('ALL ' + str(len(data.keys())) + ' MONIT SERVICES ARE OK')

        self.exit(result, data, metrics, message=' / '.join(msglist))


class MonitConn(dict):
    def __init__(self, host='localhost', port=2812, username=None, password='', https=False):

        if not port:
            port = 2812

        port = int(port)
        self.baseurl = (https and 'https://%s:%i' or 'http://%s:%i') % (host, port)
        url = self.baseurl + '/_status?format=xml'

        req = urllib2.Request(url)

        if username:
            base64string = base64.encodestring('%s:%s' % (username, password))[:-1]
            authheader = "Basic %s" % base64string
            req.add_header("Authorization", authheader)

        try:
            handle = urllib2.urlopen(req)
        except urllib2.URLError as e:
            raise Exception(e.reason)

        try:
            response = handle.read()
        except:
            raise Exception("Error while reading")

        try:
            from xml.etree.ElementTree import XML
            root = XML(response)
        except:
            raise Exception("Error while converting to XML")

        for serv_el in root.iter('service'):
            serv = MonitConn.Service(self, serv_el)
            self[serv.name] = serv

    class Service:
        """
        Describes a Monit service, i.e. a monitored resource.
        """

        def __init__(self, daemon, xml):
            """
            Parse service from XML element.
            """
            self.xml = xml
            self.data = {}
            self.perfdata = ''
            self.name = self._xmlfind('name')
            self.type = {
                0: 'filesystem',
                1: 'directory',
                2: 'file',
                3: 'process',
                4: 'connection',
                5: 'system'
            }.get(int(xml.attrib['type']), 'unknown')
            self.daemon = daemon
            self.running = True

            if self.type != 'system':
                self.running = not bool(int(self._xmlfind('status')))

            if self.type == 'filesystem':
                self.data['percent'] = self._xmlfind('block/percent')

            elif self.type == 'system':
                cpu_user = self._xmlfind('system/cpu/user', 'float')
                cpu_system = self._xmlfind('system/cpu/system', 'float')
                cpu_wait = self._xmlfind('system/cpu/wait', 'float')

                self.data['cpu'] = int(cpu_user + cpu_system + cpu_wait)
                self.data['memory'] = self._xmlfind('system/memory/percent')
                self.data['swap'] = self._xmlfind('system/swap/percent')

            elif self.type == 'process':
                self.data['memory'] = self._xmlfind('memory/percent')
                self.data['cpu'] = self._xmlfind('cpu/percent')
                self.data['childrens'] = self._xmlfind('children')

            elif self.type == 'file':
                self.data['size'] = self._xmlfind('size')

            self.monitored = bool(int(self._xmlfind('monitor')))

        def _xmlfind(self, key, kind= 'text'):
            retval = ''
            try:
                retval = self.xml.find(kind).text
                if kind == 'float':
                    retval = float(retval)

                if kind == 'int':
                    retval = int(retval)

            except:
                pass

            if not retval and kind != 'text':
                retval = 0

            return retval

        def __repr__(self):
            repren = self.type.capitalize()
            if not self.running is None:
                repren += self.running and ', running' or ', stopped'

            if not self.monitored is None:
                repren += self.monitored and ', monitored' or ', not monitored'

            return repren

if __name__ == '__main__':
    monitor = Monit()
    monitor.run()
