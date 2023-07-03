import functools
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
import typing_extensions

FORMAT_STR_DETAILED = '%(asctime)s - {%(name)s:%(lineno)s} - {%(levelname)s:%(threadName)s} - %(message)s'
FORMAT_STR_SHORT = '%(asctime)s - %(message)s'
RAMDISK_PATH = str(Path(__file__).resolve().parents[2]) + '/ramdisk/'


def filter_neg(name: str, record) -> bool:
    if name in record.threadName:
        return False
    return True


def filter_pos(name: str, record) -> bool:
    if name in record.threadName:
        return True
    return False


def setup_logging() -> None:
    def mb_to_bytes(megabytes: int) -> int:
        return megabytes * 1000000
    main_file_handler = RotatingFileHandler(RAMDISK_PATH + 'main.log', maxBytes=mb_to_bytes(4), backupCount=1)
    main_file_handler.setFormatter(logging.Formatter(FORMAT_STR_DETAILED))
    logging.basicConfig(level=logging.DEBUG, handlers=[main_file_handler])
    logging.getLogger().handlers[0].addFilter(functools.partial(filter_neg, "soc"))
    logging.getLogger().handlers[0].addFilter(functools.partial(filter_neg, "Internal Chargepoint"))
    logging.getLogger().handlers[0].addFilter(functools.partial(filter_neg, "smarthome"))

    mqtt_log = logging.getLogger("mqtt")
    mqtt_log.propagate = False
    mqtt_file_handler = RotatingFileHandler(RAMDISK_PATH + 'mqtt.log', maxBytes=mb_to_bytes(3), backupCount=1)
    mqtt_file_handler.setFormatter(logging.Formatter(FORMAT_STR_SHORT))
    mqtt_log.addHandler(mqtt_file_handler)

    smarthome_log_handler = RotatingFileHandler(RAMDISK_PATH + 'smarthome.log', maxBytes=mb_to_bytes(2), backupCount=1)
    smarthome_log_handler.setFormatter(logging.Formatter(FORMAT_STR_SHORT))
    smarthome_log_handler.addFilter(functools.partial(filter_pos, "smarthome"))
    logging.getLogger().addHandler(smarthome_log_handler)

    soc_log_handler = RotatingFileHandler(RAMDISK_PATH + 'soc.log', maxBytes=mb_to_bytes(2), backupCount=1)
    soc_log_handler.setFormatter(logging.Formatter(FORMAT_STR_DETAILED))
    soc_log_handler.addFilter(functools.partial(filter_pos, "soc"))
    logging.getLogger().addHandler(soc_log_handler)

    internal_chargepoint_log_handler = RotatingFileHandler(RAMDISK_PATH + 'internal_chargepoint.log',
                                                           maxBytes=mb_to_bytes(4),
                                                           backupCount=1)
    internal_chargepoint_log_handler.setFormatter(logging.Formatter(FORMAT_STR_DETAILED))
    internal_chargepoint_log_handler.addFilter(functools.partial(filter_pos, "Internal Chargepoint"))
    logging.getLogger().addHandler(internal_chargepoint_log_handler)

    urllib3_log = logging.getLogger("urllib3.connectionpool")
    urllib3_log.propagate = True
    urllib3_file_handler = RotatingFileHandler(RAMDISK_PATH + 'soc.log', maxBytes=mb_to_bytes(5), backupCount=1)
    urllib3_file_handler.setFormatter(logging.Formatter(FORMAT_STR_DETAILED))
    urllib3_file_handler.addFilter(functools.partial(filter_pos, "soc"))
    urllib3_log.addHandler(urllib3_file_handler)

    logging.getLogger("pymodbus").setLevel(logging.WARNING)


log = logging.getLogger(__name__)


class ModifyLoglevelContext:
    def __init__(self, logger: logging.Logger, new_loglevel: int):
        self.logger = logger
        self.new_loglevel = new_loglevel

    def __enter__(self):
        self.previous_loglevel = self.logger.level
        self.logger.setLevel(self.new_loglevel)

    def __exit__(self, exception_type, exception, exception_traceback) -> typing_extensions.Literal[False]:
        self.logger.setLevel(self.previous_loglevel)
        # no exception handling
        return False
