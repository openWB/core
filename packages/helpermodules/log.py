"""Singelton für das Logger-Modul
"""

import logging
from pathlib import Path
import subprocess


def setup_logging(name):
    root_logger = logging.getLogger(name)
    # Only do something if logging is not yet initialized.
    # It may not be initialized if this function is called multiple times or of logging is set up while unit testing
    if not root_logger.hasHandlers():
        handler = logging.FileHandler(str(Path(__file__).resolve().parents[2] / 'ramdisk' / (name+'.log')))
        handler.setFormatter(
            logging.Formatter(
                '%(asctime)s - {%(pathname)s:%(lineno)s} - %(levelname)s - %(message)s')
        )
        root_logger.addHandler(handler)
        root_logger.setLevel(logging.DEBUG)
    return root_logger


class MainLogger:
    class __Logger:
        logger = setup_logging("main")

        def __init__(self):
            pass

        def info(self, message: str, exception=None):
            self.logger.info(message, exc_info=exception)

        def debug(self, message: str, exception=None):
            self.logger.debug(message, exc_info=exception)

        def error(self, message: str, exception=None):
            self.logger.error(message, exc_info=exception)

        def warning(self, message: str, exception=None):
            self.logger.warning(message, exc_info=exception)

        def critical(self, message: str, exception=None):
            self.logger.critical(message, exc_info=exception)

        def exception(self, message: str):
            self.logger.exception(message)

        def setLevel(self, level):
            level_conversion = {0: logging.WARNING, 1: logging.INFO, 2: logging.DEBUG}
            self.logger.setLevel(level_conversion[level])

    instance = None

    def __new__(cls):
        if not MainLogger.instance:
            MainLogger.instance = MainLogger.__Logger()
        return MainLogger.instance


class MqttLogger:
    class __Logger:
        logger = setup_logging("mqtt")

        def __init__(self):
            pass

        def info(self, message: str, exception=None):
            self.logger.info(message, exc_info=exception)

        def debug(self, message: str, exception=None):
            self.logger.debug(message, exc_info=exception)

        def error(self, message: str, exception=None):
            self.logger.error(message, exc_info=exception)

        def warning(self, message: str, exception=None):
            self.logger.warning(message, exc_info=exception)

        def critical(self, message: str, exception=None):
            self.logger.critical(message, exc_info=exception)

        def exception(self, message: str):
            self.logger.exception(message)

        def setLevel(self, level):
            level_conversion = {0: logging.WARNING, 1: logging.INFO, 2: logging.DEBUG}
            self.logger.setLevel(level_conversion[level])

    instance = None

    def __new__(cls):
        if not MqttLogger.instance:
            MqttLogger.instance = MqttLogger.__Logger()
        return MqttLogger.instance


def cleanup_logfiles():
    """ ruft das Skript zum Kürzen der Logfiles auf.
    """
    MainLogger().debug("Logdateien kuerzen")
    parent_file = Path(__file__).resolve().parents[2]
    subprocess.run([str(parent_file / "runs" / "cleanup_log.sh"), str(parent_file / "ramdisk" / "main.log")])
    subprocess.run([str(parent_file / "runs" / "cleanup_log.sh"), str(parent_file / "ramdisk" / "mqtt.log")])
