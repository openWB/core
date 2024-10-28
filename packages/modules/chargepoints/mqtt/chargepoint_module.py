import logging

from helpermodules.utils.error_handling import CP_ERROR, ErrorTimerContext
from modules.chargepoints.mqtt.config import Mqtt
from modules.common.abstract_chargepoint import AbstractChargepoint
from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_context import SingleComponentUpdateContext
from modules.common.fault_state import ComponentInfo, FaultState

log = logging.getLogger(__name__)


class ChargepointModule(AbstractChargepoint):
    def __init__(self, config: Mqtt) -> None:
        self.config = config
        self.fault_state = FaultState(ComponentInfo(
            self.config.id,
            "Ladepunkt", "chargepoint"))
        self.client_error_context = ErrorTimerContext(
            f"openWB/set/chargepoint/{self.config.id}/get/error_timestamp", CP_ERROR, hide_exception=True)

    def set_current(self, current: float) -> None:
        log.debug("MQTT-Ladepunkte abonnieren die Soll-Stromstärke direkt vom Broker.")

    def get_values(self) -> None:
        with SingleComponentUpdateContext(self.fault_state):
            log.debug("MQTT-Ladepunkte müssen nicht ausgelesen werden.")

    def switch_phases(self, phases_to_use: int, duration: int) -> None:
        log.warning("Phasenumschaltung für MQTT-Ladepunkte nicht unterstützt.")


chargepoint_descriptor = DeviceDescriptor(configuration_factory=Mqtt)
