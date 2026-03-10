#!/usr/bin/env python3
import logging
from typing import TypedDict, Any
from modules.common.abstract_device import AbstractBat
from modules.common.component_state import BatState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.modbus import ModbusDataType, ModbusTcpClient_
from modules.common.store import get_bat_value_store
from modules.devices.solakon.solakon_one.config import SolakonOneBatSetup

log = logging.getLogger(__name__)


class KwargsDict(TypedDict):
    client: ModbusTcpClient_


class SolakonOneBat(AbstractBat):
    def __init__(self, component_config: SolakonOneBatSetup, **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.client: ModbusTcpClient_ = self.kwargs['client']
        self.store = get_bat_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))

    def update(self) -> None:
        unit = self.component_config.configuration.modbus_id

        # AC Leistung am Stecker, Batterie aus dem Netz aufladen hat positive Werte,
        # Leistung aus der Batterie und/oder aus PV ins Netz abgeben hat negative Werte
        power = self.client.read_holding_registers(39134, ModbusDataType.INT_32, unit=unit) * -1
        # SoC Ladezustand der Batterie in %
        soc = self.client.read_holding_registers(39424, ModbusDataType.INT_16, unit=unit)
        # gesamte DC Ladung der Batterie in Wh
        imported = self.client.read_holding_registers(39605, ModbusDataType.UINT_32, unit=unit) * 10
        # gesamte DC Entladung der Batterie in Wh
        exported = self.client.read_holding_registers(39609, ModbusDataType.UINT_32, unit=unit) * 10

        bat_state = BatState(
            power=power,
            soc=soc,
            imported=imported,
            exported=exported
        )
        self.store.set(bat_state)


component_descriptor = ComponentDescriptor(configuration_factory=SolakonOneBatSetup)
