#!/usr/bin/python3
import time
from modules.chargepoints.ip_evse.config import IpEvseOpenWB

from modules.common import modbus
from modules.common.abstract_chargepoint import AbstractChargepoint
from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_context import SingleComponentUpdateContext
from modules.common.fault_state import ComponentInfo
from modules.common.store import get_chargepoint_value_store
from modules.common.component_state import ChargepointState


class ChargepointModule(AbstractChargepoint):
    def __init__(self, config: IpEvseOpenWB) -> None:
        self.config = config
        ip_address = self.config.configuration.ip_address
        self.__client = modbus.ModbusClient(ip_address, 8899)
        self.store = get_chargepoint_value_store(self.config.id)
        self.component_info = ComponentInfo(
            self.config.id,
            "Ladepunkt", "chargepoint")

    def get_values(self) -> None:
        with SingleComponentUpdateContext(self.component_info):
            modbus_id = self.config.configuration.modbus_id

            rq = self.__client.delegate.read_holding_registers(1002, 1, unit=modbus_id)
            state = int(rq.registers[0])

            if state > 1:
                plug_state = True
            else:
                plug_state = False
            if plug_state > 2:
                charge_state = True
            else:
                charge_state = False

            chargepoint_state = ChargepointState(
                plug_state=plug_state,
                charge_state=charge_state)
            self.store.set(chargepoint_state)

    def set_current(self, current: float) -> None:
        with SingleComponentUpdateContext(self.component_info):
            self.__client.delegate.write_registers(
                1000, current, unit=self.config.configuration.modbus_id)

    def switch_phases(self, phases_to_use: int, duration: int) -> None:
        with SingleComponentUpdateContext(self.component_info):
            modbus_id = self.config.configuration.modbus_id
            if (phases_to_use == 1):
                self.__client.delegate.write_register(0x0001, 256, unit=modbus_id)
                time.sleep(duration)
                self.__client.delegate.write_register(0x0001, 512, unit=modbus_id)

            elif (phases_to_use == 3):
                self.__client.delegate.write_register(0x0002, 256, unit=modbus_id)
                time.sleep(duration)
                self.__client.delegate.write_register(0x0002, 512, unit=modbus_id)

    def perform_cp_interruption(self, duration: int) -> None:
        with SingleComponentUpdateContext(self.component_info):
            modbus_id = self.config.configuration.modbus_id
            self.__client.delegate.write_register(0x0001, 256, unit=modbus_id)
            time.sleep(duration)
            self.__client.delegate.write_register(0x0001, 512, unit=modbus_id)


chargepoint_descriptor = DeviceDescriptor(configuration_factory=IpEvseOpenWB)
