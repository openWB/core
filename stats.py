"""Log-Funktionen
"""

from datetime import datetime

ramdiskdir = '/var/www/html/openWB/ramdisk/'


class stats():
    """ schreibt Logdateien und das Ladelog.
    """

    def write_log(self):
        """ Erstellung des Ladelogs
        """
        pass

    def write_charge_log(self):
        """ Schreiben des Ladelogs
        """
        pass

    def log_mqtt(self, msg):
        """log all messages before any error forces this process to die
        """
        if (len(msg.payload.decode("utf-8")) >= 1):
            theTime = datetime.now()
            timestamp = theTime.strftime(format = "%Y-%m-%d %H:%M:%S")
            file = open(ramdiskdir+'mqtt.log', 'a')
            file.write( "%s Topic: %s Message: %s\n" % (timestamp, msg.topic, str(msg.payload.decode("utf-8"))) )
            file.close()