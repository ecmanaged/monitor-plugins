#!/usr/bin/env python

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'plugins'))

from __mplugin import MPlugin
from __mplugin import OK, CRITICAL

import_error = False
try:
    import MySQLdb as Database
except:
    import_error = True


class CheckMySQLSlave(MPlugin):
    def mysql_repchk(self, host, port, user, password):

        try:
            conn = Database.connect(host=host, port=int(port), user=user, passwd=password, connect_timeout=10)
        except:
            self.exit(CRITICAL, message="Unable to connect to MySQL Database")
        try:
            conn_cursor = conn.cursor(Database.cursors.DictCursor)
            conn_cursor.execute('SHOW SLAVE STATUS;')
            result = conn_cursor.fetchall()
        except:
            self.exit(CRITICAL, message="Unable to run SHOW SLAVE STATUS")

        return result[0]

    def run(self):
        if import_error:
            self.exit(CRITICAL, message="Please install python-mysqldb or MySQL-python")

        host = self.config.get('host')
        user = self.config.get('user')
        password = self.config.get('password')
        port = self.config.get('port', 3306)

        if not host:
            self.exit(CRITICAL, message="Please provide host")

        if not user or not password:
            self.exit(CRITICAL, message="Please provide user and password")

        data = self.mysql_repchk(host, port, user, password)

        if not data:
            self.exit(CRITICAL, message="status ERROR: metric SLAVE_STATUS string NOT_CONFIGURED")

        if "Slave_SQL_Running_State" in data:
            self.exit(CRITICAL, message=data["Slave_SQL_Running_State"])

        metrics = {
            'Seconds Behind Master': {
                'Seconds Behind Master' : data['Seconds_Behind_Master']
            }
        }

        if data["Slave_IO_Running"] == "Yes" and data["Slave_SQL_Running"] == "Yes":
            self.exit(OK, data, metrics)
        else:
            self.exit(CRITICAL, message="Slvae IO or Slave SQL is not running")


if __name__ == '__main__':
    monitor = CheckMySQLSlave()
    monitor.run()




