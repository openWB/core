import json
import sys
from typing import Dict


def update_hardware_configuration(new_setting: Dict) -> None:
    with open("/home/openwb/configuration.json", "r") as f:
        data = json.loads(f.read())
    with open("/home/openwb/configuration.json", "w") as f:
        data.update(new_setting)
        f.write(json.dumps(data))


def get_hardware_configuration_setting(name: str):
    with open("/home/openwb/configuration.json", "r") as f:
        return json.loads(f.read())[name]


if __name__ == "__main__":
    update_hardware_configuration(json.loads(sys.argv[1]))
