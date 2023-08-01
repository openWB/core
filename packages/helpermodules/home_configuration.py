import json
from typing import Dict


def update_home_configuration(new_setting: Dict) -> None:
    with open("/home/openwb/configuration.json", "r") as f:
        data = json.loads(f.read())
    with open("/home/openwb/configuration.json", "w") as f:
        data.update(new_setting)
        f.write(json.dumps(data))


def get_home_configuration_setting(name: str):
    with open("home/openwb/configuration.json", "r") as f:
        return json.loads(f.read())[name]
