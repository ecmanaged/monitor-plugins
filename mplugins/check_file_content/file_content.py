#!/usr/bin/env python

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'plugins'))

from __mplugin import MPlugin
from __mplugin import OK, WARNING, CRITICAL, UNKNOWN, TIMEOUT

import os

BLOCKSIZE = 65536

class CheckFileContent(MPlugin):
    def run(self):
        file = self.config.get('file_path')
        if not file:
            self.exit(CRITICAL, message="Invalid config")

        if not os.path.isfile(file):
            self.exit(CRITICAL, message="File not found")

        # Build hashes
        content = ''
        with open(file, 'rb') as afile:
            buf = afile.read(BLOCKSIZE)
            while len(buf) > 0:
                content += str(buf)
                buf = afile.read(BLOCKSIZE)

        data = {
            'content': content,
        }

        self.exit(OK, data)

if __name__ == '__main__':
    monitor = CheckFileContent()
    monitor.run()
