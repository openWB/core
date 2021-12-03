from typing import Dict

from helpermodules.log import MainLogger
from modules.common.abstract_chargepoint import AbstractChargepoint


def get_default_config() -> Dict:
    return {"connection_module": {
        "type": "mqtt",
        "configuration":
        {"id": 0}
    },
        "power_module": {}}


class ChargepointModule(AbstractChargepoint):
    def __init__(self, connection_module: dict, power_module: dict) -> None:
        self.connection_module = connection_module
        self.power_module = power_module

    def set_current(self, current: float) -> None:
        MainLogger().debug("MQTT-Ladepunkte subscriben die Daten direkt vom Broker.")

    def get_values(self) -> None:
        MainLogger().debug("MQTT-Ladepunkte müssen nicht ausgelesen werden.")
