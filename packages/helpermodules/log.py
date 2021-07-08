"""Log-Modul, dass die KOnfiguration für die Log-Dateien und Funktionen zum Aufruf der einzelnen Handler enthält
"""

import filelock
import logging
import traceback

debug_logger = None
debug_fhandler = None
debug_lock = None
data_logger = None
data_fhandler = None
data_lock = None


def setup_logger():
    global debug_logger
    global debug_fhandler
    global debug_lock
    debug_logger, debug_fhandler = _config_logger("debug")
    debug_lock = filelock.FileLock('/var/www/html/openWB/debug.log.lock')
    global data_logger
    global data_fhandler
    global data_lock
    data_logger, data_fhandler = _config_logger("data")
    data_lock = filelock.FileLock('/var/www/html/openWB/data.log.lock')


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
    return logger, fh

def message_debug_log(level, message):
    with debug_lock.acqiure(timeout=1):
        _set_message(debug_logger, level, message)
        debug_fhandler.close()

def message_data_log(level, message):
    with data_lock.acquire(timeout=1):
        _set_message(data_logger, level, message)
        data_fhandler.close()


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