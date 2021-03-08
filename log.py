"""Log-Modul, dass die KOnfiguration für die Log-Dateien und Funktionen zum Aufruf der einzelnen Handler enthält
"""

import inspect
import logging

debug_logger = None


def setup_logger():
    global debug_logger
    debug_logger = _config_logger("debug")


def _config_logger(name):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh = logging.FileHandler('/var/www/html/openWB/ramdisk/'+name+'.log')
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    ch.setFormatter(formatter)
    logger.addHandler(ch)
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

def log_key_error(key):
    print("KeyError "+str(key)+" in "+inspect.stack()[1][3]+" in Module "+inspect.getmodulename(inspect.stack()[1][1]))

def log_key_error_loop(key, loop):
    print("KeyError "+str(key)+" related to loop-object "+str(loop)+" in "+inspect.stack()[1][3]+" in Module "+inspect.getmodulename(inspect.stack()[1][1]))