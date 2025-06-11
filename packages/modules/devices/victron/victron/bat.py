#!/usr/bin/env python3
import logging
from typing import Any, Optional, TypedDict

from modules.common import modbus
from modules.common.abstract_device import AbstractBat
from modules.common.component_state import BatState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.modbus import ModbusDataType
from modules.common.simcount import SimCounter
from modules.common.store import get_bat_value_store
from modules.devices.victron.victron.config import VictronBatSetup

log = logging.getLogger(__name__)


class KwargsDict(TypedDict):
    device_id: int
    client: modbus.ModbusTcpClient_


class VictronBat(AbstractBat):
    def __init__(self, component_config: VictronBatSetup, **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.__device_id: int = self.kwargs['device_id']
        self.__tcp_client: modbus.ModbusTcpClient_ = self.kwargs['client']
        self.sim_counter = SimCounter(self.__device_id, self.component_config.id, prefix="speicher")
        self.store = get_bat_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))
        self.last_mode = 'Undefined'

    def update(self) -> None:
        modbus_id = self.component_config.configuration.modbus_id
        with self.__tcp_client:
            power = self.__tcp_client.read_holding_registers(842, ModbusDataType.INT_16, unit=modbus_id)
            soc = self.__tcp_client.read_holding_registers(843, ModbusDataType.UINT_16, unit=modbus_id)

        imported, exported = self.sim_counter.sim_count(power)
        bat_state = BatState(
            power=power,
            soc=soc,
            imported=imported,
            exported=exported
        )
        self.store.set(bat_state)

    def set_power_limit(self, power_limit: Optional[int]) -> None:
        modbus_id = self.component_config.configuration.modbus_id

        # Wenn Victron Dynamic ESS aktiv, erfolgt keine weitere Regelung in openWB
        dynamic_ess_mode = self.__tcp_client.read_holding_registers(5400, ModbusDataType.UINT_16, unit=modbus_id)
        if dynamic_ess_mode == 1:
            log.debug("Dynamic ESS Mode ist aktiv, daher erfolgt keine Regelung des Speichers durch openWB")
            return

        if power_limit is None:
            log.debug("Keine Batteriesteuerung, Selbstregelung durch Wechselrichter")
            if self.last_mode is not None:
                # ESS Mode 1 für Selbstregelung mit Phasenkompensation setzen
                self.__tcp_client.write_registers(39, [0], data_type=ModbusDataType.UINT_16, unit=228)
                self.__tcp_client.write_registers(2902, [1], data_type=ModbusDataType.UINT_16, unit=modbus_id)
                self.last_mode = None
        elif power_limit == 0:
            log.debug("Aktive Batteriesteuerung. Batterie wird auf Stop gesetzt und nicht entladen")
            if self.last_mode != 'stop':
                # ESS Mode 3 für externe Steuerung und keine Entladung
                self.__tcp_client.write_registers(2902, [3], data_type=ModbusDataType.UINT_16, unit=modbus_id)
                self.__tcp_client.write_registers(39, [1], data_type=ModbusDataType.UINT_16, unit=228)
                self.last_mode = 'stop'
        elif power_limit > 0:
            if self.last_mode != 'discharge':
                # ESS Mode 3 für externe Steuerung und auf L1 wird entladen
                self.__tcp_client.write_registers(2902, [3], data_type=ModbusDataType.UINT_16, unit=modbus_id)
                self.__tcp_client.write_registers(39, [0], data_type=ModbusDataType.UINT_16, unit=228)
                self.last_mode = 'discharge'
            # Die maximale Entladeleistung begrenzen auf 5000W
            power_value = int(min(power_limit, 5000))
            log.debug(f"Aktive Batteriesteuerung. Batterie wird mit {power_value} W entladen")
            self.__tcp_client.write_registers(37, [power_value & 0xFFFF], data_type=ModbusDataType.INT_16, unit=228)

    def power_limit_controllable(self) -> bool:
        return True


component_descriptor = ComponentDescriptor(configuration_factory=VictronBatSetup)
