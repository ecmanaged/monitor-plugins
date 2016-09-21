#!/usr/bin/env python

import shlex
import subprocess

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'plugins'))

from __mplugin import MPlugin
from __mplugin import OK, CRITICAL


class RunCmd(MPlugin):
    def run(self):
        cmd = self.config.get('command')
        
        if not cmd:
            self.exit(CRITICAL, message="Invalid command")
        
        result, stdout = self._run_command(cmd)
        if result: result = CRITICAL

        data = {}
        metrics = {}
        if self._is_number(stdout):
            data['result_num'] = stdout
            data['result_str'] = None
            
            # Metric only if is numeric
            metrics = {
              'result': {
                'result': data['result_num']
              }
            }    

        elif self._is_string(stdout):
            data['result_str'] = stdout
            data['result_num'] = None

        else:
            self.exit(CRITICAL, message="Unsupported result")

        self.exit(result, data, metrics)

    def _run_command(self, cmd):
        commands = cmd.split('|')

        # Ensure we get full output
        myenv = os.environ.copy()
        myenv["COLUMNS"] = "2000"
                
        result = 2
        stdout, stderr = '',''
        
        for command in commands:
            try:
                p = subprocess.Popen(
                    shlex.split(command),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    stdin=subprocess.PIPE,
                    bufsize=0,
                    env=myenv,
                    universal_newlines=True,
                    close_fds=(os.name == 'posix')
                )

                if stdout:
                    p.stdin.write(stdout)
                    
                stdout,stderr = p.communicate()
                result = p.wait()

            except Exception as e:
                self.exit(CRITICAL, message="Unable to run command: " + str(e))

        stdout = stdout.rstrip('\n')
        if result and not stdout and stderr:
            stdout = stderr

	# Try to conver string to int / float
	try: stdout = int(stdout)
	except ValueError:
	    try: stdout = float(stdout)
            except ValueError: pass

        return result, stdout
    
monitor = RunCmd()
monitor.run()
