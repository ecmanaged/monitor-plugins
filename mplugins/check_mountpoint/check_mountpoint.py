#!/usr/bin/env python

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'plugins'))

from __mplugin import MPlugin
from __mplugin import OK, CRITICAL

class CheckMountPoint(MPlugin):
    def run(self):
        mountpoint = self.config.get('mountpoint')

        if os.path.ismount(mountpoint):
            self.exit(OK, message=mountpoint + " is mounted")
        else:
            self.exit(CRITICAL, message=mountpoint + ' is not mounted')

if __name__ == '__main__':
    monitor = CheckMountPoint()
    monitor.run()
    
