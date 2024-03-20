import json
import sys
from typing import Dict

HARDWARE_CONFIGURATION_FILE = "/home/openwb/configuration.json"


def _read_configuration() -> Dict:
    with open(HARDWARE_CONFIGURATION_FILE, "r") as f:
        return json.loads(f.read())


def update_hardware_configuration(new_setting: Dict) -> None:
    data = _read_configuration()
    with open(HARDWARE_CONFIGURATION_FILE, "w") as f:
        data.update(new_setting)
        f.write(json.dumps(data))


def remove_setting_hardware_configuration(obsolet_setting: str) -> None:
    data = _read_configuration()
    if obsolet_setting in data:
        with open(HARDWARE_CONFIGURATION_FILE, "w") as f:
            data.pop(obsolet_setting)
            f.write(json.dumps(data))


def get_hardware_configuration_setting(name: str, default=None):
    return _read_configuration().get(name, default)


def exists_hardware_configuration_setting(name: str) -> bool:
    return name in _read_configuration()


def get_serial_number() -> str:
    try:
        with open("/home/openwb/snnumber", "r") as file:
            return file.read().replace("\n", "")
    except FileNotFoundError:
        return "noSerialNumber"


if __name__ == "__main__":
    update_hardware_configuration(json.loads(sys.argv[1]))
