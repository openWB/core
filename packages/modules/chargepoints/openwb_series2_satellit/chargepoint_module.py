#!/usr/bin/python3
# import asyncio
import logging
# import telnetlib3
import telnetlib
# import time
from typing import Optional

from modules.chargepoints.openwb_series2_satellit.config import OpenWBseries2Satellit
from modules.common import modbus
from modules.common.abstract_chargepoint import AbstractChargepoint
from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_context import SingleComponentUpdateContext
from modules.common.evse import Evse
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.sdm import Sdm630
from modules.common.store import get_chargepoint_value_store
from modules.common.component_state import ChargepointState

log = logging.getLogger(__name__)


class ChargepointModule(AbstractChargepoint):
    VALID_VERSIONS = ["openWB Satellit 2.0"]

    def __init__(self, config: OpenWBseries2Satellit) -> None:
        self.config = config
        self.component_info = ComponentInfo(self.config.id, "Ladepunkt", "chargepoint")
        self.version: Optional[bool] = None
        with SingleComponentUpdateContext(self.component_info):
            client = modbus.ModbusTcpClient_(self.config.configuration.ip_address, 8899)
            self._evse_client = Evse(1, client)
            self._evse_client.get_firmware_version()
            self._counter_client = self._counter_client_factory(client)
            self.store = get_chargepoint_value_store(self.config.id)
            self._validate_version()

    def _validate_version(self):
        # telnetlib ist ab Python 3.11 deprecated
        try:
            with telnetlib.Telnet(self.config.configuration.ip_address, 8898) as client:
                answer = client.read_until(bytearray("openWB Satellit 2.0", 'utf-8'), 2)
            parsed_answer = answer.decode("utf-8").split("\r\n")[-1]
            for version in self.VALID_VERSIONS:
                if version in parsed_answer:
                    self.version = True
                    log.debug("Firmware des openWB satellit ist mit openWB software2 kompatibel.")
                else:
                    self.version = False
                    raise ValueError
        except (ConnectionRefusedError, ValueError):
            raise FaultState.error(
                "Firmware des openWB satellit ist nicht mit openWB software2 kompatibel. "
                "Bitte den Support kontaktieren.")
        # Verbindungen werden nicht geschlossen
        # def get_or_create_eventloop() -> asyncio.AbstractEventLoop:
        #     try:
        #         return asyncio.get_event_loop()
        #     except RuntimeError:
        #         loop = asyncio.new_event_loop()
        #         asyncio.set_event_loop(loop)
        #         return asyncio.get_event_loop()
        # loop = get_or_create_eventloop()
        # coro = telnetlib3.open_connection(self.config.configuration.ip_address, 8898, shell=self._shell)
        # reader, writer = loop.run_until_complete(coro)
        # loop.run_until_complete(writer.protocol.waiter_closed)
        # time.sleep(2)
        # writer.close()
        # reader.close()

    # async def _shell(self, reader: telnetlib3.TelnetReader, writer: telnetlib3.TelnetWriter):
    #     for i in range(0, 3):
    #         try:
    #             outp = await asyncio.wait_for(reader.readline(), timeout=3)
    #         except asyncio.exceptions.TimeoutError:
    #             # writer.close()
    #             raise FaultState.error(
    #                 "Firmware des openWB satellit ist nicht mit openWB software2 kompatibel. "
    #                 "Bitte den Support kontaktieren.")
    #         if not outp:
    #             # End of File
    #             break
    #         for version in self.VALID_VERSIONS:
    #             if version in outp:
    #                 self.version = True
    #                 log.debug("Firmware des openWB satellit ist mit openWB software2 kompatibel.")
    #                 return
    #     else:
    #         self.version = False
    #         raise ValueError

    def _counter_client_factory(self, client: modbus.ModbusTcpClient_) -> Sdm630:
        if self.config.configuration.counter_type == "sdm630":
            return Sdm630(105, client)
        else:
            raise FaultState.error(f'Unbekannter Zählertyp {self.config.configuration.counter_type}')

    def get_values(self) -> None:
        if self.version is not None:
            with SingleComponentUpdateContext(self.component_info):
                if self.version is False:
                    raise FaultState.error(
                        "Firmware des openWB Satellit ist nicht mit openWB 2 kompatibel. "
                        "Bitte den Support kontaktieren.")
                with self._counter_client.client:
                    currents = self._counter_client.get_currents()
                phases_in_use = sum(1 for current in currents if current > 3)
                with self._evse_client.client:
                    plug_state, charge_state, _ = self._evse_client.get_plug_charge_state()

                chargepoint_state = ChargepointState(
                    power=self._counter_client.get_power()[1],
                    currents=currents,
                    imported=self._counter_client.get_imported(),
                    exported=0,
                    voltages=self._counter_client.get_voltages(),
                    plug_state=plug_state,
                    charge_state=charge_state,
                    phases_in_use=phases_in_use,
                )
                self.store.set(chargepoint_state)

    def set_current(self, current: float) -> None:
        with SingleComponentUpdateContext(self.component_info, update_always=False):
            with self._evse_client.client:
                if self.version:
                    self._evse_client.set_current(int(current))
                else:
                    self._evse_client.set_current(0)


chargepoint_descriptor = DeviceDescriptor(configuration_factory=OpenWBseries2Satellit)
