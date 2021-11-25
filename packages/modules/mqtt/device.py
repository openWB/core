#!/usr/bin/env python3
""" Modul zum Auslesen von Alpha Ess Speichern, Zählern und Wechselrichtern.
"""
from typing import List
import sys

from helpermodules import log
from modules.common import modbus
from modules.mqtt import bat
from modules.mqtt import counter
from modules.mqtt import inverter


def get_default() -> dict:
    return {
        "name": "Alpha ESS",
        "type": "alpha_ess",
        "id": None,
        "configuration": {}
    }


class Device():
    def __init__(self, device_config: dict) -> None:
        try:
            super().__init__()
            self.data = {}
            self.data["config"] = device_config
            self.client = None
            self.data["components"] = []
            for c in self.data["config"]["components"]:
                component = self.data["config"]["components"][c]
                factory = self.__component_factory(component["type"])
                self.data["components"].append(factory(self.client, component))
        except Exception as e:
            log.MainLogger().error("Fehler im Modul "+self.data["config"]["name"], e)

    def add_component(self, component_config: dict) -> None:
        try:
            factory = self.__component_factory(component_config["type"])
            self.data["components"]["component"+str(component_config["id"])
                                    ] = factory(self.data["config"]["id"], self.client, component_config)
        except Exception:
            log.MainLogger().exception("Fehler im Modul "+self.data["config"]["name"])

    def __component_factory(self, component_type: str):
        try:
            if component_type == "bat":
                return bat.AlphaEssBat
            elif component_type == "counter":
                return counter.AlphaEssCounter
            elif component_type == "inverter":
                return inverter.AlphaEssInverter
        except Exception as e:
            log.MainLogger().error("Fehler im Modul "+self.data["config"]["name"], e)

    def read(self):
        try:
            log.MainLogger().debug("Komponenten von "+self.data["config"]["name"]+" auslesen.")
            for component in self.data["components"]:
                component.read()
        except Exception as e:
            log.MainLogger().error("Fehler im Modul "+self.data["config"]["name"], e)


def read_legacy(argv: List):
    try:
        component_type = str(argv[1])
        version = int(argv[2])

        default = get_default()
        default["id"] = 0
        dev = Device(default)
        component_default = globals()[component_type].get_default()
        component_default["id"] = 0
        component_default["configuration"]["version"] = version
        dev.add_component(component_default)

        log.MainLogger().debug('alpha_ess Version: ' + str(version))

        dev.read()
    except Exception as e:
        log.MainLogger().error("Fehler im Modul Alpha Ess", e)


if __name__ == "__main__":
    try:
        read_legacy(sys.argv)
    except Exception as e:
        log.MainLogger().error("Fehler im Alpha Ess-Skript", e)
