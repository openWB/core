"""Log-Modul, dass die KOnfiguration für die Log-Dateien und Funktionen zum Aufruf der einzelnen Handler enthält
"""

import logging

debug_logger = None


def setup_logger():
    global debug_logger
    debug_logger = _config_logger("debug")


def _config_logger(name):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    fh = logging.FileHandler('/var/www/html/openWB/ramdisk/'+name+'.log')
    fh.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    return logger


def message_debug_log(level, message):
    _set_message(debug_logger, level, message)


def _set_message(logger, level, message):
    if level == "debug":
        logger.debug(message)
    elif level == "info":
        logger.info(message)
    elif level == "warning":
        logger.warning(message)
    elif level == "error":
        logger.error(message)
    elif level == "critical":
        logger.critical(message)
