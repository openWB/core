#!/usr/bin/env python3
import logging
from dataclass_utils import dataclass_from_dict
from modules.common.abstract_device import AbstractBat
from modules.common.component_state import BatState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.modbus import ModbusDataType, ModbusTcpClient_
from modules.common.store import get_bat_value_store
from modules.devices.fox_ess.fox_ess.config import FoxEssBatSetup

log = logging.getLogger(__name__)


class FoxEssBat(AbstractBat):
    def __init__(self, component_config: FoxEssBatSetup) -> None:
        self.component_config = dataclass_from_dict(FoxEssBatSetup, component_config)
        self.store = get_bat_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))

    def update(self, client: ModbusTcpClient_) -> None:
        unit = self.component_config.configuration.modbus_id

        power = client.read_holding_registers(31036, ModbusDataType.INT_16, unit=unit) * -1
        soc = client.read_holding_registers(31038, ModbusDataType.UINT_16, unit=unit)
        # Geladen in kWh * 0,1
        imported = client.read_holding_registers(32003, ModbusDataType.UINT_32, unit=unit) * 100
        # Entladen in kWh * 0,1
        exported = client.read_holding_registers(32006, ModbusDataType.UINT_32, unit=unit) * 100

        bat_state = BatState(
            power=power,
            soc=soc,
            imported=imported,
            exported=exported
        )
        self.store.set(bat_state)


component_descriptor = ComponentDescriptor(configuration_factory=FoxEssBatSetup)
