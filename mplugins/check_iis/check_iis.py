#!/usr/bin/env python

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'plugins'))

from __mplugin import MPlugin
from __mplugin import OK, CRITICAL

wmi_import_error = False
try:
    import wmi
except:
    wmi_import_error = True

class CheckIIS(MPlugin):
    def get_stats(self):
        wmi_cls = None
        try:
            wmi_conn = wmi.WMI()
            wmi_cls = wmi_conn.Win32_PerfFormattedData_W3SVC_WebService()
        except:
            pass
        return  wmi_cls

    def run(self):
        if wmi_import_error:
            self.exit(CRITICAL, message="please install wmi(pip install wmi) and pywin32(https://sourceforge.net/projects/pywin32/files/pywin32/Build%20220/pywin32-220.win32-py2.7.exe/download)")

        stat = self.get_stats()
        if not stat:
            self.exit(CRITICAL, message="Unable fetch stats")

        counter_data = [
            'TotalBytesSent',
            'TotalBytesReceived',
            'TotalBytesTransferred',
            'TotalFilesSent',
            'TotalFilesReceived',
            'TotalConnectionAttemptsAllInstances',
            'TotalGetRequests',
            'TotalPostRequests',
            'TotalHeadRequests',
            'TotalPutRequests',
            'TotalDeleteRequests',
            'TotalOptionsRequests',
            'TotalTraceRequests',
            'TotalNotFoundErrors',
            'TotalLockedErrors',
            'TotalAnonymousUsers',
            'TotalNonAnonymousUsers',
            'TotalCGIRequests',
            'TotalISAPIExtensionRequests'
        ]

        gauge_data = [
            'CurrentConnections'
        ]

        data = {}
        for iis_site in stat:
            if iis_site.Name == '_Total':
                for attr in counter_data:
                    try:
                        data[attr] = float(getattr(iis_site, attr))
                    except:
                        data[attr] = 0

                for attr in gauge_data:
                    try:
                        data[attr] = float(getattr(iis_site, attr))
                    except:
                        data[attr] = 0

        tmp_counter = {}
        for idx in counter_data:
            try:
                tmp_counter[idx] = int(data.get(idx, 0))
            except:
                tmp_counter[idx] = data.get(idx, 0)

        tmp_counter = self.counters(tmp_counter, 'iis')

        tmp_gauge = {}
        for idx in gauge_data:
            try:
                tmp_gauge[idx] = int(data.get(idx, 0))
            except:
                tmp_gauge[idx] = data.get(idx, 0)

        data = tmp_counter.copy()
        data.update(tmp_gauge)

        metrics = {
            'Network': {
                'TotalBytesSent': data['TotalBytesSent'],
                'TotalBytesReceived': data['TotalBytesReceived'],
                'TotalBytesTransferred': data['TotalBytesTransferred'],
                'CurrentConnections': data['CurrentConnections'],
                'TotalFilesSent': data['TotalFilesSent'],
                'TotalFilesReceived': data['TotalFilesReceived'],
                'TotalConnectionAttemptsAllInstances': data['TotalConnectionAttemptsAllInstances']
                },
            'Errors': {
                'TotalNotFoundErrors': data['TotalNotFoundErrors'],
                'TotalLockedErrors': data['TotalLockedErrors']
                },
            'Users': {
                'TotalAnonymousUsers': data['TotalAnonymousUsers'],
                'TotalNonAnonymousUsers': data['TotalNonAnonymousUsers']
                },
            'Requests': {
                'TotalCGIRequests': data['TotalCGIRequests'],
                'TotalISAPIExtensionRequests': data['TotalISAPIExtensionRequests']
                }
        }

        self.exit(OK, data, metrics)

if __name__ == '__main__':
    monitor = CheckIIS()
    monitor.run()