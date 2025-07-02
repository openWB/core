
import logging
import time

from helpermodules.utils.error_handling import CP_ERROR, ErrorTimerContext
from modules.chargepoints.openwb_pro.config import OpenWBPro
from modules.common.abstract_chargepoint import AbstractChargepoint
from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_context import SingleComponentUpdateContext
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.hardware_check import check_meter_values
from modules.common.store import get_chargepoint_value_store
from modules.common.component_state import ChargepointState
from modules.common import req
from modules.internal_chargepoint_handler.internal_chargepoint_handler_config import InternalChargepoint

log = logging.getLogger(__name__)


class ChargepointModule(AbstractChargepoint):
    WRONG_CHARGE_STATE = "Lade-Status ist nicht aktiv, aber Strom fließt."
    WRONG_PLUG_STATE = "Ladepunkt ist nicht angesteckt, aber es wird geladen."

    def __init__(self, config: OpenWBPro) -> None:
        self.config = config
        self.store = get_chargepoint_value_store(self.config.id)
        self.fault_state = FaultState(ComponentInfo(
            self.config.id,
            "Ladepunkt", "chargepoint"))
        self.__session = req.get_http_session()
        self.client_error_context = ErrorTimerContext(
            f"openWB/set/chargepoint/{self.config.id}/get/error_timestamp", CP_ERROR, hide_exception=True)

        with SingleComponentUpdateContext(self.fault_state, update_always=False):
            self.__session.post(
                'http://' + self.config.configuration.ip_address + '/connect.php',
                data={'heartbeatenabled': '1'})

    def set_internal_context_handlers(self, hierarchy_id: int, internal_cp: InternalChargepoint, parent_hostname: str):
        self.fault_state = FaultState(ComponentInfo(
            self.config.id,
            "Ladepunkt "+str(self.config.id),
            "internal_chargepoint",
            hierarchy_id=hierarchy_id,
            parent_hostname=parent_hostname))
        self.client_error_context = ErrorTimerContext(
            f"openWB/set/internal_chargepoint/{self.config.id}/get/error_timestamp", CP_ERROR, hide_exception=True)
        self.client_error_context.error_timestamp = internal_cp.get.error_timestamp

    def set_current(self, current: float) -> None:
        if self.client_error_context.error_counter_exceeded():
            current = 0
        with SingleComponentUpdateContext(self.fault_state, update_always=False):
            with self.client_error_context:
                ip_address = self.config.configuration.ip_address
                self.__session.post('http://'+ip_address+'/connect.php', data={'ampere': current})

    def get_values(self) -> None:
        with SingleComponentUpdateContext(self.fault_state):
            chargepoint_state = self.request_values()
            if chargepoint_state is not None:
                # bei Fehler, aber Fehlezähler noch nicht abgelaufen, keine Werte mehr publishen.
                self.store.set(chargepoint_state)

    def request_values(self) -> ChargepointState:
        with self.client_error_context:
            ip_address = self.config.configuration.ip_address
            json_rsp = self.__session.get('http://'+ip_address+'/connect.php').json()

            chargepoint_state = ChargepointState(
                power=json_rsp["power_all"],
                powers=json_rsp["powers"],
                currents=json_rsp["currents"],
                imported=json_rsp["imported"],
                exported=json_rsp["exported"],
                plug_state=json_rsp["plug_state"],
                charge_state=json_rsp["charge_state"],
                phases_in_use=json_rsp["phases_in_use"],
                vehicle_id=json_rsp["vehicle_id"],
                evse_current=json_rsp["offered_current"],
                serial_number=json_rsp["serial"]
            )

            if json_rsp.get("voltages"):
                meter_msg = check_meter_values(json_rsp["voltages"])
                if meter_msg:
                    self.fault_state.warning(meter_msg)
                chargepoint_state.voltages = json_rsp["voltages"]
            if json_rsp.get("soc_value"):
                chargepoint_state.soc = json_rsp["soc_value"]
            if json_rsp.get("soc_timestamp"):
                chargepoint_state.soc_timestamp = json_rsp["soc_timestamp"]
            if json_rsp.get("frequency"):
                chargepoint_state.frequency = json_rsp["frequency"]
            if json_rsp.get("rfid_tag"):
                chargepoint_state.rfid = json_rsp["rfid_tag"]
            if json_rsp.get("rfid_timestamp"):
                chargepoint_state.rfid_timestamp = json_rsp["rfid_timestamp"]

            self.validate_values(chargepoint_state)
            self.client_error_context.reset_error_counter()
            return chargepoint_state
        if self.client_error_context.error_counter_exceeded():
            chargepoint_state = ChargepointState()
            chargepoint_state.plug_state = False
            chargepoint_state.charge_state = False
            chargepoint_state.imported = None  # bei None werden keine Werte gepublished
            chargepoint_state.exported = None
            return chargepoint_state
        else:
            return None

    def validate_values(self, chargepoint_state: ChargepointState) -> None:
        if chargepoint_state.charge_state is False and max(chargepoint_state.currents) > 1:
            raise ValueError(self.WRONG_CHARGE_STATE)
        if chargepoint_state.plug_state is False and chargepoint_state.power > 20:
            raise ValueError(self.WRONG_PLUG_STATE)

    def switch_phases(self, phases_to_use: int, duration: int) -> None:
        with SingleComponentUpdateContext(self.fault_state, update_always=False):
            with self.client_error_context:
                ip_address = self.config.configuration.ip_address
                response = self.__session.get('http://'+ip_address+'/connect.php')
                if response.json()["phases_target"] != phases_to_use:
                    ip_address = self.config.configuration.ip_address
                    self.__session.post('http://'+ip_address+'/connect.php',
                                        data={'phasetarget': str(1 if phases_to_use == 1 else 3)})
                    time.sleep(duration)

    def clear_rfid(self) -> None:
        pass


chargepoint_descriptor = DeviceDescriptor(configuration_factory=OpenWBPro)
