#!/usr/bin/python3
import logging
import time
from typing import Optional

from control import data
from helpermodules.utils.error_handling import CP_ERROR, ErrorTimerContext
from modules.chargepoints.openwb_series2_satellit.config import OpenWBseries2Satellit
from modules.common import modbus
from modules.common.abstract_chargepoint import AbstractChargepoint
from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_context import SingleComponentUpdateContext
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.store import get_chargepoint_value_store
from modules.common.component_state import ChargepointState
from modules.common.version_by_telnet import get_version_by_telnet
from modules.internal_chargepoint_handler.clients import EVSE_ID_CP0, EVSE_ID_ONE_BUS_CP1, ClientHandler

log = logging.getLogger(__name__)


class ChargepointModule(AbstractChargepoint):
    VALID_MODELS = {
        "type": "openWB Satellit",
        "versions": ["2.0"]
    }
    # 1/3 des Regelintervalls für Abfrage der Werte, davon die Hälfte je Duo-LP
    CP1_DELAY = data.data.general_data.data.control_interval / 6
    CP1_DELAY_STARTUP = 4
    ID_PHASE_SWITCH_UNIT = 3

    def __init__(self, config: OpenWBseries2Satellit) -> None:
        self.config = config
        self.fault_state = FaultState(ComponentInfo(self.config.id, "Ladepunkt", "chargepoint"))
        self.version: Optional[bool] = None
        with SingleComponentUpdateContext(self.fault_state):
            self.delay_second_cp(self.CP1_DELAY_STARTUP)
            self.store = get_chargepoint_value_store(self.config.id)
            self.client_error_context = ErrorTimerContext(
                f"openWB/set/chargepoint/{self.config.id}/get/error_timestamp", CP_ERROR, hide_exception=True)
            self._create_client()
            self._validate_version()
        self.max_evse_current = self._client.evse_client.get_max_current()

    def delay_second_cp(self, delay: float):
        if self.config.configuration.duo_num == 0:
            return
        else:
            time.sleep(delay)

    def _create_client(self):
        self._client = ClientHandler(
            self.config.configuration.duo_num,
            modbus.ModbusTcpClient_(self.config.configuration.ip_address, 8899),
            EVSE_ID_CP0 if self.config.configuration.duo_num == 0 else EVSE_ID_ONE_BUS_CP1,
            self.fault_state)

    def _validate_version(self):
        try:
            parsed_answer = get_version_by_telnet(
                f'{self.VALID_MODELS["type"]} {self.VALID_MODELS["versions"][0]}', self.config.configuration.ip_address)
            for version in self.VALID_MODELS["versions"]:
                if version in parsed_answer:
                    self.version = True
                    log.debug("Firmware des openWB satellit ist mit openWB software2 kompatibel.")
                else:
                    self.version = False
                    raise ValueError
        except (ConnectionRefusedError, ValueError) as e:
            e.args += (("Firmware des openWB satellit ist nicht mit openWB software2 kompatibel. "
                        "Bitte den Support kontaktieren."),)
            raise e

    def get_values(self) -> None:
        with SingleComponentUpdateContext(self.fault_state):
            if self.version is not None:
                with self.client_error_context:
                    try:
                        self.delay_second_cp(self.CP1_DELAY)
                        with self._client.client:
                            self._client.check_hardware(self.fault_state)
                            if self.version is False:
                                self._validate_version()
                            currents = self._client.meter_client.get_currents()
                            phases_in_use = sum(1 for current in currents if current > 3)
                            plug_state, charge_state, _ = self._client.evse_client.get_plug_charge_state()

                            chargepoint_state = ChargepointState(
                                power=self._client.meter_client.get_power()[1],
                                currents=currents,
                                imported=self._client.meter_client.get_imported(),
                                exported=0,
                                voltages=self._client.meter_client.get_voltages(),
                                plug_state=plug_state,
                                charge_state=charge_state,
                                phases_in_use=phases_in_use,
                                serial_number=self._client.meter_client.get_serial_number(),
                                max_evse_current=self.max_evse_current
                            )
                        self.store.set(chargepoint_state)
                        self.client_error_context.reset_error_counter()
                    except AttributeError:
                        self._create_client()
                        self._validate_version()
            else:
                self._create_client()
                self._validate_version()

    def set_current(self, current: float) -> None:
        if self.version is not None:
            if self.client_error_context.error_counter_exceeded():
                current = 0
            with SingleComponentUpdateContext(self.fault_state, update_always=False):
                with self.client_error_context:
                    try:
                        self.delay_second_cp(self.CP1_DELAY)
                        with self._client.client:
                            self._client.check_hardware(self.fault_state)
                            if self.version:
                                self._client.evse_client.set_current(int(current))
                            else:
                                self._client.evse_client.set_current(0)
                    except AttributeError:
                        self._create_client()
                        self._validate_version()

    def switch_phases(self, phases_to_use: int, duration: int) -> None:
        if self.version is not None:
            with SingleComponentUpdateContext(self.fault_state, update_always=False):
                with self.client_error_context:
                    try:
                        with self._client.client:
                            self._client.check_hardware(self.fault_state)
                            if phases_to_use == 1:
                                self._client.client.delegate.write_register(
                                    0x0001, 256, unit=self.ID_PHASE_SWITCH_UNIT)
                                time.sleep(1)
                                self._client.client.delegate.write_register(
                                    0x0001, 512, unit=self.ID_PHASE_SWITCH_UNIT)
                            else:
                                self._client.client.delegate.write_register(
                                    0x0002, 512, unit=self.ID_PHASE_SWITCH_UNIT)
                                time.sleep(1)
                                self._client.client.delegate.write_register(
                                    0x0002, 256, unit=self.ID_PHASE_SWITCH_UNIT)
                    except AttributeError:
                        self._create_client()
                        self._validate_version()


chargepoint_descriptor = DeviceDescriptor(configuration_factory=OpenWBseries2Satellit)
