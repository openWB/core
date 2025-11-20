#!/usr/bin/env python3
import logging
from typing import TypedDict, Any

from modules.common.abstract_device import AbstractBat
from modules.common.component_state import BatState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.modbus import ModbusDataType, ModbusTcpClient_
from modules.common.store import get_bat_value_store
from modules.devices.solis.solis.config import SolisBatSetup

log = logging.getLogger(__name__)


class KwargsDict(TypedDict):
    client: ModbusTcpClient_


class SolisBat(AbstractBat):
    def __init__(self, component_config: SolisBatSetup, **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.client: ModbusTcpClient_ = self.kwargs['client']
        self.store = get_bat_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))

    def update(self) -> None:
        unit = self.component_config.configuration.modbus_id

        power = self.client.read_input_registers(33149, ModbusDataType.INT_32, device_id=unit)
        soc = self.client.read_input_registers(33139, ModbusDataType.UINT_16, device_id=unit)
        # Geladen in kWh
        imported = self.client.read_input_registers(33161, ModbusDataType.UINT_32, device_id=unit) * 1000
        # Entladen in kWh
        exported = self.client.read_input_registers(33165, ModbusDataType.UINT_32, device_id=unit) * 1000

        bat_state = BatState(
            power=power,
            soc=soc,
            imported=imported,
            exported=exported
        )
        self.store.set(bat_state)


component_descriptor = ComponentDescriptor(configuration_factory=SolisBatSetup)
