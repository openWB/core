"""Singelton für das Logger-Modul
"""

import logging
import subprocess

debug_logger = None
debug_fhandler = None
debug_lock = None
data_logger = None
data_fhandler = None
data_lock = None
mqtt_logger = None
mqtt_fhandler = None
mqtt_lock = None


class MainLogger:
    instance = None

    def __init__(self):
        if not MainLogger.instance:
            MainLogger.instance = logging.getLogger("main")
            MainLogger.instance.setLevel(logging.DEBUG)
            formatter = logging.Formatter(
                '%(asctime)s - {%(pathname)s:%(lineno)s} - %(levelname)s - %(message)s')
            fh = logging.FileHandler(
                '/var/www/html/openWB/ramdisk/main.log')
            fh.setLevel(logging.DEBUG)
            fh.setFormatter(formatter)
            MainLogger.instance.addHandler(fh)

    def __getattr__(self, name):
        return getattr(self.instance, name)


class MqttLogger:
    instance = None

    def __init__(self):
        if not MqttLogger.instance:
            MqttLogger.instance = logging.getLogger("mqtt")
            MqttLogger.instance.setLevel(logging.DEBUG)
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            fh = logging.FileHandler('/var/www/html/openWB/ramdisk/mqtt.log')
            fh.setLevel(logging.DEBUG)
            fh.setFormatter(formatter)
            MqttLogger.instance.addHandler(fh)

    def __getattr__(self, name):
        return getattr(self.instance, name)


def cleanup_logfiles():
    """ ruft das Skript zum Kürzen der Logfiles auf.
    """
    subprocess.run(["./runs/cleanup_log.sh", "./runs/main.log"])
    subprocess.run(["./runs/cleanup_log.sh", "./runs/mqtt.log"])
