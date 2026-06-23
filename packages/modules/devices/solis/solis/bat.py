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
from modules.devices.solis.solis.config import SolisBatSetup
from modules.devices.solis.solis.version import SolisVersion
from modules.common.utils.peak_filter import PeakFilter
from modules.common.component_type import ComponentType

log = logging.getLogger(__name__)


class KwargsDict(TypedDict):
    client: ModbusTcpClient_
    device_id: int
    version: SolisVersion


class SolisBat(AbstractBat):
    def __init__(self, component_config: SolisBatSetup, **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.client: ModbusTcpClient_ = self.kwargs['client']
        self.version: SolisVersion = self.kwargs['version']
        self.sim_counter = SimCounter(self.kwargs['device_id'], self.component_config.id, prefix="speicher")
        self.store = get_bat_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))
        self.peak_filter = PeakFilter(ComponentType.BAT, self.component_config.id, self.fault_state)

    def update(self) -> None:
        unit = self.component_config.configuration.modbus_id

        power = self.client.read_input_registers(33149, ModbusDataType.INT_32, unit=unit)
        soc = self.client.read_input_registers(33139, ModbusDataType.UINT_16, unit=unit)
        bat_current = self.client.read_input_registers(33134, ModbusDataType.INT_16, unit=unit) * 0.1
        current_direction = self.client.read_input_registers(33135, ModbusDataType.UINT_16, unit=unit)
        if current_direction == 1:
            bat_current = -bat_current
            power = -power

        currents = [bat_current / 3] * 3

        self.peak_filter.check_values(power)
        imported, exported = self.sim_counter.sim_count(power)
        bat_state = BatState(
            power=power,
            soc=soc,
            currents=currents,
            imported=imported,
            exported=exported
        )
        self.store.set(bat_state)

    def set_power_limit(self, power_limit: Optional[int]) -> None:
        unit = self.component_config.configuration.modbus_id

        if power_limit is None:
            self.client.write_register(43135, 0, data_type=ModbusDataType.UINT_16, unit=unit)
            log.debug("Keine Batteriesteuerung, Selbstregelung durch Wechselrichter")
        elif power_limit == 0:
            self.client.write_register(43135, 1, data_type=ModbusDataType.UINT_16, unit=unit)
            self.client.write_register(43136, 0, data_type=ModbusDataType.UINT_16, unit=unit)
            log.debug("Aktive Batteriesteuerung. Batterie wird auf Stop gesetzt und nicht geladen/entladen")
        elif power_limit < 0:
            self.client.write_register(43135, 2, data_type=ModbusDataType.UINT_16, unit=unit)
            power_value = int(abs(power_limit) / 10)
            self.client.write_register(43129, power_value, data_type=ModbusDataType.UINT_16, unit=unit)
            log.debug(f"Aktive Batteriesteuerung. Batterie wird mit {power_value} W entladen für den Hausverbrauch")
        elif power_limit > 0:
            self.client.write_register(43135, 1, data_type=ModbusDataType.UINT_16, unit=unit)
            power_value = int(power_limit / 10)
            self.client.write_register(43136, power_value, data_type=ModbusDataType.UINT_16, unit=unit)
            log.debug(f"Aktive Batteriesteuerung. Batterie wird mit {power_value} W geladen")

    def power_limit_controllable(self) -> bool:
        # Nur die S-Serie sollte die Speichersteuerung können
        return self.version == SolisVersion.hybrid_s


component_descriptor = ComponentDescriptor(configuration_factory=SolisBatSetup)
