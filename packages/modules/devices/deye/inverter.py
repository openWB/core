#!/usr/bin/env python3
from typing import Dict, Union

from dataclass_utils import dataclass_from_dict
from modules.common.component_state import InverterState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo
from modules.common.modbus import ModbusDataType, ModbusTcpClient_
from modules.common.store import get_inverter_value_store
from modules.devices.deye.config import DeyeInverterSetup


class DeyeInverter:
    def __init__(self, component_config: Union[Dict, DeyeInverterSetup]) -> None:
        self.component_config = dataclass_from_dict(DeyeInverterSetup, component_config)
        self.store = get_inverter_value_store(self.component_config.id)
        self.component_info = ComponentInfo.from_component_config(self.component_config)

    def update(self, client: ModbusTcpClient_) -> None:
        # hier wird er aus der Konfiguration übernommen; bei bat.py und counter ist er fix auf 1 gestellt
        # es können aber bis zu 15 WR in Serie (parallel) geschalten werden
        # kann diese ID nicht "durchgereicht" werden ?
        unit = self.component_config.configuration.modbus_id

        # Wechselrichter hat 2 mppt Tracker
        power_in1 = sum(client.read_holding_registers(672, ModbusDataType.INT_16, unit=unit))
        power_in2 = sum(client.read_holding_registers(673, ModbusDataType.INT_16, unit=unit))
        power = power_in1 + power_in2

        # Gesamt Produktion Wechselrichter unsigned integer in Wh
        exported = client.read_holding_registers(534, ModbusDataType.UINT_16, unit=unit)

        inverter_state = InverterState(
            power=power,
            exported=exported,
        )
        self.store.set(inverter_state)


component_descriptor = ComponentDescriptor(configuration_factory=DeyeInverterSetup)
