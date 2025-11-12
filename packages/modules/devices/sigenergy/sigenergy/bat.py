#!/usr/bin/env python3
import logging
from typing import TypedDict, Any, Optional
from modules.common.abstract_device import AbstractBat
from modules.common.component_state import BatState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.modbus import ModbusDataType, ModbusTcpClient_
from modules.common.simcount import SimCounter
from modules.common.store import get_bat_value_store
from modules.devices.sigenergy.sigenergy.config import SigenergyBatSetup

log = logging.getLogger(__name__)


class KwargsDict(TypedDict):
    device_id: int
    client: ModbusTcpClient_


class SigenergyBat(AbstractBat):
    def __init__(self, component_config: SigenergyBatSetup, **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.__device_id: int = self.kwargs['device_id']
        self.client: ModbusTcpClient_ = self.kwargs['client']
        self.store = get_bat_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))
        self.sim_counter = SimCounter(self.__device_id, self.component_config.id, prefix="speicher")
        self.last_mode = 'Undefined'

    def update(self) -> None:
        unit = self.component_config.configuration.modbus_id

        power = self.client.read_holding_registers(30037, ModbusDataType.INT_32, unit=unit)
        # soc unit 0.1%
        soc = self.client.read_holding_registers(30014, ModbusDataType.UINT_16, unit=unit) / 10
        imported, exported = self.sim_counter.sim_count(power)

        bat_state = BatState(
            power=power,
            soc=soc,
            imported=imported,
            exported=exported
        )
        self.store.set(bat_state)

    def set_power_limit(self, power_limit: Optional[int]) -> None:
        unit = self.component_config.configuration.modbus_id
        log.debug(f'last_mode: {self.last_mode}')
        # Steuerung erfolgt über SoC (mit Faktor 10)
        if power_limit is None:
            log.debug("Keine Batteriesteuerung, Selbstregelung durch Wechselrichter")
            if self.last_mode is not None:
                # Entladesperre ab 5%, Ansonsten Eigenregelung
                self.__tcp_client.write_registers(40048, [50], data_type=ModbusDataType.UINT_16, unit=unit)
                self.last_mode = None
        else:
            log.debug("Aktive Batteriesteuerung. Batterie wird auf Stop gesetzt und nicht entladen")
            if self.last_mode != 'stop':
                # Entladesperre auch bei 100% SoC
                self.__tcp_client.write_registers(40048, [1000], data_type=ModbusDataType.UINT_16, unit=unit)
                self.last_mode = 'stop'

    def power_limit_controllable(self) -> bool:
        return True


component_descriptor = ComponentDescriptor(configuration_factory=SigenergyBatSetup)
