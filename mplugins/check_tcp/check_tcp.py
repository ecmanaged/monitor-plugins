#!/usr/bin/env python

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'plugins'))

from __mplugin import MPlugin
from __mplugin import OK, WARNING, CRITICAL, UNKNOWN, TIMEOUT

import socket
from time import time

class CheckTCP(MPlugin):
    def run(self):
        host = self.config.get('host')
        port = self.config.get('port')
        
        if not host or not port:
           self.exit(CRITICAL, message="Invalid configuration")
           
        # Set timeout
        timeout = self.config.get('timeout',TIMEOUT)
        socket.setdefaulttimeout(int(timeout))
        
        #create an AF_INET, STREAM socket (TCP)
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        except socket.error, msg:
            self.exit(CRITICAL, message="Failed to create socket: " + msg[1])
            
        # Resolve
        try:
            remote_ip = socket.gethostbyname(host)
        except socket.gaierror:
            self.exit(CRITICAL, message="Hostname could not be resolved")

        # Connect
        start_time = time()
        try:
            s.connect((remote_ip,int(port)))
        except socket.error, msg:
            self.exit(CRITICAL, message="%s" %msg[1])
        except:
            self.exit(CRITICAL, message="Unable to connect")
            
        # Try to send something
        try :
            s.sendall('\n')
        except socket.error:
            self.exit(WARNING, message="Socket opened but send failed")
            
        # Close and return    
        s.close()
        
        # Time spent
        mytime = "%.2f" % (time() - start_time)
        
        data = {
            'time': mytime,
        }
        
        metrics = {
            'Connection time': {
              'time': str(mytime)
            }
        }
        
        self.exit(OK,data,metrics)
        
        
monitor = CheckTCP()
monitor.run()
