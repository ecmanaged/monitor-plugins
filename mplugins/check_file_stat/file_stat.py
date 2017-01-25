#!/usr/bin/env python

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'plugins'))

from __mplugin import MPlugin
from __mplugin import OK, WARNING, CRITICAL, UNKNOWN, TIMEOUT

import os

try:
    import hashlib
except ImportError:
    pass

BLOCKSIZE = 65536

class CheckFile(MPlugin):
    def run(self):
        file = self.config.get('file_path')
        if not file:
            self.exit(CRITICAL, message="Invalid config")

        if not os.path.isfile(file):
            self.exit(CRITICAL, message="File not found")

        # Build hashes
        try:
            hasher_md5 = hashlib.md5()
            hasher_sha1 = hashlib.sha1()

            # Read file in blocksizes (do not waste memory)
            with open(file, 'rb') as afile:
                buf = afile.read(BLOCKSIZE)
                while len(buf) > 0:
                    hasher_md5.update(buf)
                    hasher_sha1.update(buf)
                    buf = afile.read(BLOCKSIZE)

            md5sum, sha1sum = hasher_md5.hexdigest(), hasher_sha1.hexdigest()

        except:
            md5sum, sha1sum = '', ''


        # Read stat
        (mode, ino, dev, nlink, uid, gid, size, atime, mtime, ctime) = os.stat(file)

        data = {
            'md5': md5sum,
            'sha1': sha1sum,
            'mode': mode,
            'ino': ino,
            'dev': dev,
            'nlink': nlink,
            'uid': uid,
            'gid': gid,
            'size': size,
            'atime': atime,
            'mtime': mtime,
            'ctime': ctime,
        }

        metrics = {
            'File size': {
                'size': str(size) + 'B'
            }
        }

        self.exit(OK, data, metrics)

if __name__ == '__main__':
    monitor = CheckFile()
    monitor.run()
