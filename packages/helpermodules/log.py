"""Singelton für das Logger-Modul
"""

import logging
from pathlib import Path
import subprocess


class MainLogger:
    instance = None  # type: logging.Logger

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

    def set_log_level(self, level):
        level_conversion = {0: logging.WARNING, 1: logging.INFO, 2: logging.DEBUG}
        MainLogger.instance.setLevel(level_conversion[level])

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
    MainLogger().debug("Logdateien kuerzen")
    parent_file = Path(__file__).resolve().parents[2]
    subprocess.run([str(parent_file / "runs" / "cleanup_log.sh"), str(parent_file / "ramdisk" / "main.log")])
    subprocess.run([str(parent_file / "runs" / "cleanup_log.sh"), str(parent_file / "ramdisk" / "mqtt.log")])
