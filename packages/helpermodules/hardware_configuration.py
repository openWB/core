import json
import sys
from typing import Dict

from helpermodules.utils.json_file_handler import write_and_check

HARDWARE_CONFIGURATION_FILE = "/home/openwb/configuration.json"


def update_hardware_configuration(new_setting: Dict) -> None:
    with open(HARDWARE_CONFIGURATION_FILE, "r") as f:
        data = json.loads(f.read())
    write_and_check(HARDWARE_CONFIGURATION_FILE, data.update(new_setting))


def remove_setting_hardware_configuration(obsolet_setting: str) -> None:
    with open(HARDWARE_CONFIGURATION_FILE, "r") as f:
        data = json.loads(f.read())
    if obsolet_setting in data:
        write_and_check(HARDWARE_CONFIGURATION_FILE, data.pop(obsolet_setting))


def get_hardware_configuration_setting(name: str, default=None):
    with open(HARDWARE_CONFIGURATION_FILE, "r") as f:
        configuration = json.loads(f.read())
    return configuration.get(name, default)


def get_serial_number() -> str:
    try:
        with open("/home/openwb/snnumber", "r") as file:
            return file.read().replace("\n", "")
    except FileNotFoundError:
        return "noSerialNumber"


if __name__ == "__main__":
    update_hardware_configuration(json.loads(sys.argv[1]))
