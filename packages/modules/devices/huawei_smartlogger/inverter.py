#!/usr/bin/env python3
import logging
from dataclass_utils import dataclass_from_dict
from modules.common import modbus
from modules.common.component_state import InverterState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo
from modules.common.modbus import ModbusDataType
from modules.common.simcount import SimCounter
from modules.common.store import get_inverter_value_store
from modules.devices.huawei_smartlogger.config import Huawei_SmartloggerInverterSetup

log = logging.getLogger(__name__)


class Huawei_SmartloggerInverter:
    def __init__(self,
                 device_id: int,
                 component_config: Huawei_SmartloggerInverterSetup,
                 tcp_client: modbus.ModbusTcpClient_) -> None:
        self.__device_id = device_id
        self.component_config = dataclass_from_dict(Huawei_SmartloggerInverterSetup, component_config)
        self.client = tcp_client
        self.sim_counter = SimCounter(self.__device_id, self.component_config.id, prefix="pv")
        self.store = get_inverter_value_store(self.component_config.id)
        self.component_info = ComponentInfo.from_component_config(self.component_config)

    def update(self) -> None:
        modbus_id = self.component_config.configuration.modbus_id
        power = self.client.read_holding_registers(32080, ModbusDataType.INT_32, unit=modbus_id) * -1
        exported = self.client.read_holding_registers(32106, ModbusDataType.INT_32, unit=modbus_id) * 10
        inverter_state = InverterState(
            power=power,
            exported=exported
        )
        self.store.set(inverter_state)


component_descriptor = ComponentDescriptor(configuration_factory=Huawei_SmartloggerInverterSetup)
