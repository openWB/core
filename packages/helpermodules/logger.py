import functools
import logging
from pathlib import Path
import subprocess


def filter_neg(name: str, record) -> bool:
    if name in record.threadName:
        return False
    return True


def filter_pos(name: str, record) -> bool:
    if name in record.threadName:
        return True
    return False


def setup_logging() -> None:
    format_str_detailed = '%(asctime)s - {%(name)s:%(lineno)s} - {%(levelname)s:%(threadName)s} - %(message)s'
    format_str_short = '%(asctime)s - %(message)s'
    logging.basicConfig(filename=str(Path(__file__).resolve().parents[2] / 'ramdisk' / ('main.log')),
                        format=format_str_detailed,
                        level=logging.DEBUG)
    logging.getLogger().handlers[0].addFilter(functools.partial(filter_neg, "soc"))
    logging.getLogger().handlers[0].addFilter(functools.partial(filter_neg, "Internal Chargepoint"))
    logging.getLogger().handlers[0].addFilter(functools.partial(filter_neg, "smarthome"))

    mqtt_log = logging.getLogger("mqtt")
    mqtt_log.propagate = False
    mqtt_file_handler = logging.FileHandler(str(Path(__file__).resolve().parents[2] / 'ramdisk' / ('mqtt.log')))
    mqtt_file_handler.setFormatter(logging.Formatter(format_str_short))
    mqtt_log.addHandler(mqtt_file_handler)

    smarthome_log_handler = logging.FileHandler(
        str(Path(__file__).resolve().parents[2] / 'ramdisk' / ('smarthome.log')))
    smarthome_log_handler.setFormatter(logging.Formatter(format_str_short))
    smarthome_log_handler.addFilter(functools.partial(filter_pos, "smarthome"))
    logging.getLogger().addHandler(smarthome_log_handler)

    soc_log_handler = logging.FileHandler(str(Path(__file__).resolve().parents[2] / 'ramdisk' / ('soc.log')))
    soc_log_handler.setFormatter(logging.Formatter(format_str_detailed))
    soc_log_handler.addFilter(functools.partial(filter_pos, "soc"))
    logging.getLogger().addHandler(soc_log_handler)

    internal_chargepoint_log_handler = logging.FileHandler(
        str(Path(__file__).resolve().parents[2] / 'ramdisk' / ('internal_chargepoint.log')))
    internal_chargepoint_log_handler.setFormatter(logging.Formatter(format_str_detailed))
    internal_chargepoint_log_handler.addFilter(functools.partial(filter_pos, "Internal Chargepoint"))
    logging.getLogger().addHandler(internal_chargepoint_log_handler)

    urllib3_log = logging.getLogger("urllib3.connectionpool")
    urllib3_log.propagate = True
    urllib3_file_handler = logging.FileHandler(str(Path(__file__).resolve().parents[2] / 'ramdisk' / ('soc.log')))
    urllib3_file_handler.setFormatter(logging.Formatter(format_str_detailed))
    urllib3_file_handler.addFilter(functools.partial(filter_pos, "soc"))
    urllib3_log.addHandler(urllib3_file_handler)

    logging.getLogger("pymodbus").setLevel(logging.WARNING)


log = logging.getLogger(__name__)


def cleanup_logfiles():
    """ ruft das Skript zum Kürzen der Logfiles auf.
    """
    log.debug("Logdateien kürzen")
    for path in Path(_get_parent_path()/"ramdisk").glob('*.log'):
        subprocess.run([str(_get_parent_path() / "runs" / "cleanup_log.sh"), str(path)])


def _get_parent_path() -> Path:
    return Path(__file__).resolve().parents[2]
