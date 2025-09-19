
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
from modules.common.component_state import ChargepointState, CounterState
from modules.common import req
from modules.internal_chargepoint_handler.internal_chargepoint_handler_config import InternalChargepoint

log = logging.getLogger(__name__)


class EvseSignaling:
    HLC = "HLC"
    ISO15118 = "ISO15118"
    FAKE_HIGHLEVEL = "fake_highlevel"
    PWM = "PWM"


class CpInterruptionVersion:
    CP_SIGNAL_0V = "0V"
    CP_SIGNAL_minus12V = "-12V"


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
                f'http://{self.config.configuration.ip_address}/connect.php',
                data={'heartbeatenabled': '1'})

    def set_internal_context_handlers(self, hierarchy_id: int, internal_cp: InternalChargepoint):
        self.fault_state = FaultState(ComponentInfo(
            self.config.id,
            "Ladepunkt "+str(self.config.id),
            "internal_chargepoint",
            hierarchy_id=hierarchy_id))
        self.client_error_context = ErrorTimerContext(
            f"openWB/set/internal_chargepoint/{self.config.id}/get/error_timestamp", CP_ERROR, hide_exception=True)
        self.client_error_context.error_timestamp = internal_cp.get.error_timestamp

    def set_current(self, current: float) -> None:
        if self.client_error_context.error_counter_exceeded():
            current = 0
        with SingleComponentUpdateContext(self.fault_state, update_always=False):
            with self.client_error_context:
                self.__session.post(
                    f'http://{self.config.configuration.ip_address}/connect.php', data={'ampere': current})

    def get_values(self) -> None:
        with SingleComponentUpdateContext(self.fault_state):
            try:
                chargepoint_state = self.request_values()
                if chargepoint_state is not None:
                    # bei Fehler, aber Fehlezähler noch nicht abgelaufen, keine Werte mehr publishen.
                    self.store.set(chargepoint_state)
            except Exception as e:
                if self.client_error_context.error_counter_exceeded():
                    chargepoint_state = ChargepointState(plug_state=False, charge_state=False, imported=None,
                                                         # bei im-/exported None werden keine Werte gepublished
                                                         exported=None, phases_in_use=0, power=0, currents=[0]*3)
                    self.store.set(chargepoint_state)
                    raise e

    def request_values(self) -> ChargepointState:
        with self.client_error_context:
            json_rsp = self.__session.get(f'http://{self.config.configuration.ip_address}/connect.php').json()

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
                serial_number=json_rsp["serial"],
                evse_signaling=json_rsp["evse_signaling"],
            )

            if json_rsp.get("voltages"):
                check_meter_values(CounterState(voltages=json_rsp["voltages"],
                                                currents=json_rsp["currents"],
                                                powers=json_rsp["powers"],
                                                power=json_rsp["power_all"]),
                                   self.fault_state)
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
            if json_rsp.get("max_discharge_power"):
                chargepoint_state.max_discharge_power = json_rsp["max_discharge_power"]
            if json_rsp.get("max_charge_power"):
                chargepoint_state.max_charge_power = json_rsp["max_charge_power"]

            self.validate_values(chargepoint_state)
            self.client_error_context.reset_error_counter()
            return chargepoint_state

    def validate_values(self, chargepoint_state: ChargepointState) -> None:
        if chargepoint_state.charge_state is False and max(chargepoint_state.currents) > 1:
            raise ValueError(self.WRONG_CHARGE_STATE)
        if chargepoint_state.plug_state is False and chargepoint_state.power > 20:
            raise ValueError(self.WRONG_PLUG_STATE)

    def switch_phases(self, phases_to_use: int, duration: int) -> None:
        with SingleComponentUpdateContext(self.fault_state, update_always=False):
            with self.client_error_context:
                response = self.__session.get(f'http://{self.config.configuration.ip_address}/connect.php')
                if response.json()["phases_target"] != phases_to_use:
                    self.__session.post(f'http://{self.config.configuration.ip_address}/connect.php',
                                        data={'phasetarget': str(1 if phases_to_use == 1 else 3)})
                    time.sleep(duration)

    def clear_rfid(self) -> None:
        pass

    def interrupt_cp(self, duration: int) -> None:
        self.__session.post(f'http://{self.config.configuration.ip_address}/connect.php',
                            data={'cp_interrupt': True,
                                  'cp_interrupt_version': CpInterruptionVersion.CP_SIGNAL_0V,
                                  'cp_interrupt_duration': duration})


chargepoint_descriptor = DeviceDescriptor(configuration_factory=OpenWBPro)
