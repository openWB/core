import json
import sys
from typing import Dict

HARDWARE_CONFIGURATION_FILE = "/home/openwb/configuration.json"


def update_hardware_configuration(new_setting: Dict) -> None:
    with open(HARDWARE_CONFIGURATION_FILE, "r") as f:
        data = json.loads(f.read())
    with open(HARDWARE_CONFIGURATION_FILE, "w") as f:
        data.update(new_setting)
        f.write(json.dumps(data))


def remove_setting_hardware_configuration(obsolet_setting: str) -> None:
    with open(HARDWARE_CONFIGURATION_FILE, "r") as f:
        data = json.loads(f.read())
    if obsolet_setting in data:
        with open(HARDWARE_CONFIGURATION_FILE, "w") as f:
            data.pop(obsolet_setting)
            f.write(json.dumps(data))


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
