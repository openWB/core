
from enum import IntEnum
import logging

from helpermodules import hardware_configuration
from helpermodules.utils.error_counter import ErrorCounterContext
from modules.chargepoints.openwb_dc_adapter.config import OpenWBDcAdapter
from modules.common.abstract_chargepoint import AbstractChargepoint
from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_context import SingleComponentUpdateContext
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.store import get_chargepoint_value_store
from modules.common.component_state import ChargepointState
from modules.common import req

log = logging.getLogger(__name__)


class ChargingStatus(IntEnum):
    AVAILABLE = 0
    PREPARING_TAGID_READY = 1
    PREPARING_EV_READY = 2
    CHARGING = 3
    SUSPENDED_EV = 4
    SUSPENDED_EVSE = 5
    FINISHING = 6
    RESERVED = 7
    UNAVAILABLE = 8
    UNAVAILABLE_FW_UPDATE = 9
    FAULTED = 10
    UNAVAILABLE_CONN_OBJ = 11


class ChargepointModule(AbstractChargepoint):
    def __init__(self, config: OpenWBDcAdapter) -> None:
        self.config = config
        self.store = get_chargepoint_value_store(self.config.id)
        self.fault_state = FaultState(ComponentInfo(
            self.config.id,
            "Ladepunkt", "chargepoint"))
        self.__session = req.get_http_session()
        self.__client_error_context = ErrorCounterContext(
            "Anhaltender Fehler beim Auslesen des Ladepunkts. Sollstromstärke wird zurückgesetzt.")
        if hardware_configuration.get_hardware_configuration_setting("openwb_dc_adapter") is False:
            raise Exception(
                "DC-Laden muss durch den Support freigeschaltet werden. Bitte nehme Kontakt mit dem Support auf.")
        self.efficiency = None

        with SingleComponentUpdateContext(self.fault_state, False):
            with self.__client_error_context:
                self.__session.post(
                    'http://' + self.config.configuration.ip_address + '/connect.php',
                    data={'heartbeatenabled': '1'})

    def set_current(self, current: float) -> None:
        if self.__client_error_context.error_counter_exceeded():
            current = 0
        with SingleComponentUpdateContext(self.fault_state, False):
            with self.__client_error_context:
                ip_address = self.config.configuration.ip_address
                raw_current = self.subtract_conversion_loss_from_current(current)
                self.__session.post('http://'+ip_address+'/connect.php', data={'ampere': raw_current})

    def subtract_conversion_loss_from_current(self, current: float) -> float:
        return current * (self.efficiency if self.efficiency else 0.9)

    def add_conversion_loss_to_current(self, current: float) -> float:
        return current / (self.efficiency if self.efficiency else 0.9)

    def get_values(self) -> None:
        with SingleComponentUpdateContext(self.fault_state):
            with self.__client_error_context:
                ip_address = self.config.configuration.ip_address
                json_rsp = self.__session.get('http://'+ip_address+'/connect.php').json()

                chargepoint_state = ChargepointState(
                    charge_state=json_rsp["charge_state"],
                    charging_current=json_rsp["charging_current"],
                    charging_power=json_rsp["charging_power"],
                    charging_voltage=json_rsp["charging_voltage"],
                    currents=json_rsp["currents"],
                    evse_current=json_rsp["evse_current"],
                    exported=json_rsp["exported"],
                    imported=json_rsp["imported"],
                    phases_in_use=3,
                    power=json_rsp["power_all"],
                    powers=json_rsp["powers"],
                    plug_state=json_rsp["plug_state"],
                    rfid=json_rsp["rfid"],
                    soc=json_rsp["soc"],
                    soc_timestamp=json_rsp["soc_timestamp"],
                    vehicle_id=json_rsp["vehicle_id"],
                )

                if chargepoint_state.charge_state:
                    self.efficiency = chargepoint_state.charging_power / chargepoint_state.power
                else:
                    self.efficiency = None
                if not (json_rsp["state"] == ChargingStatus.AVAILABLE.value or
                        json_rsp["state"] == ChargingStatus.PREPARING_TAGID_READY.value or
                        json_rsp["state"] == ChargingStatus.PREPARING_EV_READY.value or
                        json_rsp["state"] == ChargingStatus.CHARGING.value or
                        json_rsp["state"] == ChargingStatus.FINISHING.value):
                    raise Exception(f"Ladepunkt nicht verfügbar. Status: {ChargepointState(json_rsp['state']).name}")
                self.store.set(chargepoint_state)
                self.__client_error_context.reset_error_counter()


chargepoint_descriptor = DeviceDescriptor(configuration_factory=OpenWBDcAdapter)
