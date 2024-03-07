#!/usr/bin/python3
import logging
import time
from typing import Optional

from helpermodules.utils.error_counter import ErrorCounterContext
from modules.chargepoints.openwb_series2_satellit.config import OpenWBseries2Satellit
from modules.common import modbus
from modules.common.abstract_chargepoint import AbstractChargepoint
from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_context import SingleComponentUpdateContext
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.hardware_check_context import SeriesHardwareCheckContext
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
    CP0_DELAY = 1
    CP0_DELAY_STARTUP = 4

    def __init__(self, config: OpenWBseries2Satellit) -> None:
        self.config = config
        self.fault_state = FaultState(ComponentInfo(self.config.id, "Ladepunkt", "chargepoint"))
        self.version: Optional[bool] = None
        with SingleComponentUpdateContext(self.fault_state):
            self.delay_second_cp(self.CP0_DELAY_STARTUP)
            self.store = get_chargepoint_value_store(self.config.id)
            self.__client_error_context = ErrorCounterContext(
                "Anhaltender Fehler beim Auslesen des Ladepunkts. Soll-Stromstärke wird zurückgesetzt.",
                hide_exception=True)
            self._create_client()
            self._validate_version()

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
                f'{self.VALID_MODELS["type"]}{self.VALID_MODELS["versions"][0]}', self.config.configuration.ip_address)
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
                with self.__client_error_context:
                    try:
                        with SeriesHardwareCheckContext(self._client):
                            if self.version is False:
                                raise ValueError(
                                    "Firmware des openWB Satellit ist nicht mit openWB 2 kompatibel. "
                                    "Bitte den Support kontaktieren.")
                            self.delay_second_cp(self.CP0_DELAY)
                            with self._client.client:
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
                                )
                            self.store.set(chargepoint_state)
                    except AttributeError:
                        self._create_client()
                        self._validate_version()
            else:
                self._create_client()
                self._validate_version()

    def set_current(self, current: float) -> None:
        if self.version is not None:
            with SingleComponentUpdateContext(self.fault_state, update_always=False):
                with self.__client_error_context:
                    try:
                        with SeriesHardwareCheckContext(self._client):
                            self.delay_second_cp(self.CP0_DELAY)
                            with self._client.client:
                                if self.version:
                                    self._client.evse_client.set_current(int(current))
                                else:
                                    self._client.evse_client.set_current(0)
                    except AttributeError:
                        self._create_client()
                        self._validate_version()


chargepoint_descriptor = DeviceDescriptor(configuration_factory=OpenWBseries2Satellit)
