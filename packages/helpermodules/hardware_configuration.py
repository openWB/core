import logging
import json
import sys
from typing import Dict, Optional

from helpermodules.utils.json_file_handler import write_and_check

log = logging.getLogger(__name__)

HARDWARE_CONFIGURATION_FILE = "/home/openwb/configuration.json"


def _read_configuration() -> Dict:
    for i in range(2):
        try:
            with open(HARDWARE_CONFIGURATION_FILE, "r") as f:
                config = json.loads(f.read())
            if isinstance(config, dict):
                return config
        except Exception:
            # wird im else-Zweig abgefangen
            pass
    else:
        log.error("Invalid configuration.json file. Creating new one with default values.")
        with open("./data/config/configuration.json", "r") as f:
            config_file = json.loads(f.read())
        write_and_check(HARDWARE_CONFIGURATION_FILE, config_file)
        return config_file


def update_hardware_configuration(new_setting: Dict) -> None:
    data = _read_configuration()
    data.update(new_setting)
    write_and_check(HARDWARE_CONFIGURATION_FILE, data)


def remove_setting_hardware_configuration(obsolet_setting: str) -> None:
    data = _read_configuration()
    if obsolet_setting in data:
        data.pop(obsolet_setting)
        write_and_check(HARDWARE_CONFIGURATION_FILE, data)


def get_hardware_configuration_setting(name: str, default=None):
    return _read_configuration().get(name, default)


def exists_hardware_configuration_setting(name: str) -> bool:
    return name in _read_configuration()


def get_serial_number() -> Optional[str]:
    # Inhalt der Datei snnumber:
    # Seriennummer vorhanden: snnumber=sn1234
    # keine Seriennummer: snnumber= oder Datei nicht vorhanden
    try:
        with open("/home/openwb/snnumber", "r") as file:
            serial_number = file.read().replace("snnumber=", "").replace("\n", "")
            if serial_number == "":
                return None
            else:
                return serial_number
    except FileNotFoundError:
        return None


if __name__ == "__main__":
    update_hardware_configuration(json.loads(sys.argv[1]))
