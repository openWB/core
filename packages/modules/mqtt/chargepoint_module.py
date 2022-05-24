import logging
from typing import Dict

from modules.common.abstract_chargepoint import AbstractChargepoint
from modules.common.component_context import SingleComponentUpdateContext
from modules.common.fault_state import ComponentInfo

log = logging.getLogger(__name__)


def get_default_config() -> Dict:
    return {"id": 0,
            "connection_module": {
                "type": "mqtt",
                "name": "MQTT-Ladepunkt",
                "configuration":
                {}
            },
            "power_module": {}}


class ChargepointModule(AbstractChargepoint):
    def __init__(self, id: int, connection_module: dict, power_module: dict) -> None:
        self.id = id
        self.connection_module = connection_module
        self.power_module = power_module
        self.component_info = ComponentInfo(
            self.id,
            "Ladepunkt", "chargepoint")

    def set_current(self, current: float) -> None:
        with SingleComponentUpdateContext(self.component_info):
            log.debug("MQTT-Ladepunkte subscriben die Sollstromstärke direkt vom Broker.")

    def get_values(self) -> None:
        with SingleComponentUpdateContext(self.component_info):
            log.debug("MQTT-Ladepunkte müssen nicht ausgelesen werden.")

    def switch_phases(self, phases_to_use: int, duration: int) -> None:
        log.warning("Phasenumschaltung für MQTT-Ladepunkte nicht unterstüzt.")
