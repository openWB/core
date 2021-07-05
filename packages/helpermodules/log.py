"""Log-Modul, dass die KOnfiguration für die Log-Dateien und Funktionen zum Aufruf der einzelnen Handler enthält
"""

import traceback
import logging

debug_logger = None
data_logger = None


def setup_logger():
    global debug_logger
    debug_logger = _config_logger("debug")
    global data_logger
    data_logger = _config_logger("data")


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

def message_data_log(level, message):
    _set_message(data_logger, level, message)


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

def exception_logging(exception):
    """
    Log exception by using the root logger.

    Parameters
    ----------
    exception
    """
    tb = exception.__traceback__
    value= str(exception)
    exctype=str(type(exception))
    msg="Exception type: "+exctype+" Traceback: "+str(traceback.format_tb(tb, -1))+" Details: "+value
    message_debug_log("error", msg)