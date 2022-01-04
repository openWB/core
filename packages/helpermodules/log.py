"""Singelton für das Logger-Modul
"""

import logging
from pathlib import Path
import subprocess


class PathTruncatingFormatter(logging.Formatter):
    def format(self, record):
        if 'pathname' in record.__dict__.keys():
            record.pathname = '{}'.format(record.pathname[20:])
        return super(PathTruncatingFormatter, self).format(record)


def setup_logging(name):
    root_logger = logging.getLogger(name)
    # Only do something if logging is not yet initialized.
    # It may not be initialized if this function is called multiple times or of logging is set up while unit testing
    if not root_logger.hasHandlers():
        handler = logging.FileHandler(str(Path(__file__).resolve().parents[2] / 'ramdisk' / (name+'.log')))
        handler.setFormatter(
            PathTruncatingFormatter(
                '%(asctime)s - {%(pathname)s:%(lineno)s} - %(levelname)s - %(message)s')
        )
        root_logger.addHandler(handler)
        root_logger.setLevel(logging.DEBUG)
    return root_logger


class MainLogger:

    instance: logging.Logger = None

    def __new__(cls):
        if not MainLogger.instance:
            MainLogger.instance = setup_logging("main")
        return MainLogger.instance

    def setLevel(self, level):
        MainLogger.instance.setLevel(level)


class MqttLogger:
    instance: logging.Logger = None

    def __new__(cls):
        if not MqttLogger.instance:
            MqttLogger.instance = setup_logging("mqtt")
        return MqttLogger.instance

    def setLevel(self, level):
        MainLogger.instance.setLevel(level)


def cleanup_logfiles():
    """ ruft das Skript zum Kürzen der Logfiles auf.
    """
    MainLogger().debug("Logdateien kuerzen")
    parent_file = Path(__file__).resolve().parents[2]
    subprocess.run([str(parent_file / "runs" / "cleanup_log.sh"), str(parent_file / "ramdisk" / "main.log")])
    subprocess.run([str(parent_file / "runs" / "cleanup_log.sh"), str(parent_file / "ramdisk" / "mqtt.log")])
