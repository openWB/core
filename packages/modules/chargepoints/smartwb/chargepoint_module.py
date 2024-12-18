
import time
from helpermodules.utils.error_handling import CP_ERROR, ErrorTimerContext
from modules.chargepoints.smartwb.config import SmartWB
from modules.common.abstract_chargepoint import AbstractChargepoint
from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_context import SingleComponentUpdateContext
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.store import get_chargepoint_value_store
from modules.common.component_state import ChargepointState
from modules.common import req


class ChargepointModule(AbstractChargepoint):
    def __init__(self, config: SmartWB) -> None:
        self.config = config
        self.store = get_chargepoint_value_store(self.config.id)
        self.fault_state = FaultState(ComponentInfo(
            self.config.id,
            "Ladepunkt", "chargepoint"))
        self.client_error_context = ErrorTimerContext(
            f"openWB/set/chargepoint/{self.config.id}/get/error_timestamp", CP_ERROR, hide_exception=True)
        self.phases_in_use = 1
        self.session = req.get_http_session()

    def set_current(self, current: float) -> None:
        if self.client_error_context.error_counter_exceeded():
            current = 0
        with SingleComponentUpdateContext(self.fault_state, update_always=False):
            with self.client_error_context:
                ip_address = self.config.configuration.ip_address
                timeout = self.config.configuration.timeout
                # Stromvorgabe in Hundertstel Ampere
                params = (('current', int(current*100)),)
                self.session.get('http://'+ip_address+'/setCurrent', params=params, timeout=(timeout, None))

    def get_values(self) -> None:
        with SingleComponentUpdateContext(self.fault_state):
            with self.client_error_context:
                ip_address = self.config.configuration.ip_address
                timeout = self.config.configuration.timeout
                response = self.session.get('http://'+ip_address+'/getParameters', timeout=timeout)
                json_rsp = response.json()["list"][0]

                ev_state = json_rsp["vehicleState"]
                if ev_state == 3:
                    charge_state = True
                    plug_state = True
                elif ev_state == 2:
                    charge_state = False
                    plug_state = True
                else:
                    charge_state = False
                    plug_state = False

                currents = [json_rsp["currentP1"], json_rsp["currentP2"], json_rsp["currentP3"]]

                if currents[2] > 3:
                    self.phases_in_use = 3
                elif currents[1] > 3:
                    self.phases_in_use = 2
                elif currents[0] > 3:
                    self.phases_in_use = 1

                if json_rsp.get("voltageP1"):
                    voltages = [json_rsp["voltageP1"], json_rsp["voltageP2"], json_rsp["voltageP3"]]
                else:
                    voltages = None

                if json_rsp.get("RFIDUID"):
                    if json_rsp["RFIDUID"] == "":
                        tag = None
                    else:
                        tag = json_rsp["RFIDUID"]
                else:
                    tag = None

                max_evse_current = json_rsp["maxCurrent"]

                resp = self.session.get('http://'+ip_address+'/evseHost', timeout=timeout)
                mac = resp.json()["list"][0]["mac"]

                chargepoint_state = ChargepointState(
                    power=json_rsp["actualPower"] * 1000,
                    currents=currents,
                    imported=json_rsp["meterReading"] * 1000,
                    plug_state=plug_state,
                    charge_state=charge_state,
                    phases_in_use=self.phases_in_use,
                    voltages=voltages,
                    rfid=tag,
                    serial_number=mac,
                    max_evse_current=max_evse_current
                )

                self.store.set(chargepoint_state)
                self.client_error_context.reset_error_counter()

    def clear_rfid(self) -> None:
        with SingleComponentUpdateContext(self.fault_state):
            with self.client_error_context:
                ip_address = self.config.configuration.ip_address
                timeout = self.config.configuration.timeout
                req.get_http_session().get('http://'+ip_address+'/clearRfid', timeout=(timeout, None))

    def interrupt_cp(self, duration: int) -> None:
        with SingleComponentUpdateContext(self.fault_state, update_always=False):
            with self.client_error_context:
                ip_address = self.config.configuration.ip_address
                timeout = self.config.configuration.timeout
                req.get_http_session().get(
                    f'http://{ip_address}/interruptCp?duration={duration*1000}', timeout=(timeout, None))
                time.sleep(duration)


chargepoint_descriptor = DeviceDescriptor(configuration_factory=SmartWB)
