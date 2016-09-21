#!/usr/bin/env python

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'plugins'))

from __mplugin import MPlugin
from __mplugin import OK, CRITICAL, TIMEOUT

import re
import psutil

from time import time


class CheckProcess(MPlugin):
    def run(self):
        process = self.config.get('process')

        if not process:
           self.exit(CRITICAL, message="Invalid process")

        count = 0
        total_rss = 0
        total_vms = 0
        threads = 0
        
        regex = None
        if self._is_regex_like(process):
            regex = self._regex_clean(process)
        
        for p in psutil.process_iter():
            matched = None
            
            if psutil.version_info[:2] >= (2, 0):
                pname = ' '.join(p.cmdline())
                if not pname:
                    pname = p.name()
            else:
                pname = p.cmdline
                if self._is_list(pname):
                    pname = ' '.join(pname)
                if not pname:
                    pname = p.name
                
            if regex:
                if re.search(regex,pname):
                    matched = p.pid
                    count +=1
            else:
                # Use first command line
                name = pname.split(' ')[0]
                if name == process:
		    matched = p.pid
                    count += 1
                    
                # Use process name
                elif p.name == process:
                    matched = p.pid
                    count +=1
                   
	    if matched:
	        proc = psutil.Process(matched)
	        if psutil.version_info[:2] >= (2, 0):
                    mem = proc.get_memory_info()
                    total_rss += mem.rss
                    total_vms += mem.vms
                    threads += proc.get_num_threads()
                    create_time = proc.create_time()
	            uids = proc.uids()
    	            gids = proc.gids()
	            status = proc.status()
   	            nice = proc.get_nice()
   	            
                else:
                    mem = proc.get_memory_info()
                    total_rss += mem.rss
                    total_vms += mem.vms
                    threads += proc.get_num_threads()
                    create_time = proc.create_time
	            uids = proc.uids
    	            gids = proc.gids
	            status = proc.status
   	            nice = proc.get_nice
                    nice = proc.nice
	        
        if count:
            data = {
                'processes': count,
                'threads': threads,
                'memory_rss': self.to_mb(total_rss),
    	        'memory_vms': self.to_mb(total_vms),
	        'create_time': time() - create_time,
    	        'uids': uids,
	        'gids': gids,
                'status': status,
	        'nice': nice
            }
            metrics = {
                'Processes and Threads': {
                    'processes': count,
                    'threads': threads
                },
                'Process Memory': {
                    'memory_rss': str(self.to_mb(total_rss)) + "M",
                    'memory_vms': str(self.to_mb(total_vms)) + "M"
                }
            }
            
            message = "%s processes (%s threads) found using %sM" % (count,threads,self.to_mb(total_rss))
            
            self.exit(OK,data,metrics,message)
        
        self.exit(CRITICAL,message="Process not found")
        
    @staticmethod
    def _is_regex_like(string):
        if string.startswith('/'):
            return True    
            
        return False
        
    @staticmethod
    def _regex_clean(string):
        # Clean starting and ending slash
        string = re.sub(r'(^\/)', r'', string)
        string = re.sub(r'(\/.*$)', r'', string)
        return string


monitor = CheckProcess()
monitor.run()

