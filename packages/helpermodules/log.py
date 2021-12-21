"""Singelton für das Logger-Modul
"""

import logging
from pathlib import Path
import subprocess


# def get_log_level_from_environment():
#     try:
#         return [logging.WARNING, logging.INFO, logging.DEBUG][int(os.environ.get('debug'))]
#     except (ValueError, TypeError, IndexError):
#         # TypeError if "debug" is not set (os.environ.get returns None)
#         # ValueError if `debug` is not an int
#         # IndexError if `debug` is not between 0 and 2
#         return logging.DEBUG


def setup_logging_stdout():
    root_logger = logging.getLogger("main")
    # Only do something if logging is not yet initialized.
    # It may not be initialized if this function is called multiple times or of logging is set up while unit testing
    if not root_logger.hasHandlers():
        handler = logging.FileHandler('/var/www/html/openWB/ramdisk/main.log')
        handler.setFormatter(
            logging.Formatter(
                '%(asctime)s - {%(pathname)s:%(lineno)s} - %(levelname)s - %(message)s')
        )
        root_logger.addHandler(handler)
        root_logger.setLevel(logging.DEBUG)
    return root_logger


class MainLogger:
    class __Logger:
        logger = setup_logging_stdout()

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
            # setup_logging_stdout()
            MainLogger.instance = MainLogger.__Logger()
        return MainLogger.instance

# class MainLogger:
#     instance = None  # type: logging.Logger

#     def __init__(self):
#         if not MainLogger.instance:
#             MainLogger.instance = logging.getLogger("main")
#             MainLogger.instance.setLevel(logging.DEBUG)
#             formatter = logging.Formatter(
#                 '%(asctime)s - {%(pathname)s:%(lineno)s} - %(levelname)s - %(message)s')
#             fh = logging.FileHandler(
#                 '/var/www/html/openWB/ramdisk/main.log')
#             fh.setLevel(logging.DEBUG)
#             fh.setFormatter(formatter)
#             MainLogger.instance.addHandler(fh)

#     def set_log_level(self, level):
#         level_conversion = {0: logging.WARNING, 1: logging.INFO, 2: logging.DEBUG}
#         MainLogger.instance.setLevel(level_conversion[level])

#     def __getattr__(self, name):
#         return getattr(self.instance, name)


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
