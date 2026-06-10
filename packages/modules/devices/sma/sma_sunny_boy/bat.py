#!/usr/bin/env python3
import logging
from typing import Any, TypedDict, Optional

from modules.common.abstract_device import AbstractBat
from modules.common.component_state import BatState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.modbus import ModbusTcpClient_, ModbusDataType
from modules.common.store import get_bat_value_store
from modules.devices.sma.sma_sunny_boy.config import SmaSunnyBoyBatSetup
from modules.common.simcount import SimCounter
from modules.common.utils.peak_filter import PeakFilter
from modules.common.component_type import ComponentType
from modules.devices.sma.sma_sunny_boy.version import SmaBatVersion

log = logging.getLogger(__name__)


class KwargsDict(TypedDict):
    client: ModbusTcpClient_


class SunnyBoyBat(AbstractBat):
    SMA_UINT_64_NAN = 0xFFFFFFFFFFFFFFFF  # SMA uses this value to represent NaN
    SMA_UINT32_NAN = 0xFFFFFFFF  # SMA uses this value to represent NaN

    def __init__(self, component_config: SmaSunnyBoyBatSetup, **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.__tcp_client: ModbusTcpClient_ = self.kwargs['client']
        self.sim_counter = SimCounter(self.kwargs['device_id'], self.component_config.id, prefix="speicher")
        self.store = get_bat_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))
        self.peak_filter = PeakFilter(ComponentType.BAT, self.component_config.id, self.fault_state)
        self.last_mode = 'Undefined'

    def update(self) -> None:
        unit = self.component_config.configuration.modbus_id

        if self.component_config.configuration.version in (SmaBatVersion.hybrid, SmaBatVersion.sbs):
            soc = self.__tcp_client.read_holding_registers(30845, ModbusDataType.UINT_32, unit=unit)
            charge_power = self.__tcp_client.read_holding_registers(31393, ModbusDataType.INT_32, unit=unit)
            discharge_power = self.__tcp_client.read_holding_registers(31395, ModbusDataType.INT_32, unit=unit)

            if soc == self.SMA_UINT32_NAN:
                # Es werden keine Werte geliefert, wenn die Battery leer ist oder nichts auf der DC Seite erzeugt wird.
                soc = 0
                power = 0
            else:
                if charge_power > 5:
                    power = charge_power
                else:
                    power = discharge_power * -1

            exported = self.__tcp_client.read_holding_registers(31401, ModbusDataType.UINT_64, unit=unit)
            imported = self.__tcp_client.read_holding_registers(31397, ModbusDataType.UINT_64, unit=unit)

            if exported == self.SMA_UINT_64_NAN or imported == self.SMA_UINT_64_NAN:
                raise ValueError(f'Batterie lieferte nicht plausible Werte. Export: {exported}, Import: {imported}. ',
                                 'Sobald die Batterie geladen/entladen wird sollte sich dieser Wert ändern, ',
                                 'andernfalls kann ein Defekt vorliegen.')
            imported, exported = self.peak_filter.check_values(power, imported, exported)

        elif self.component_config.configuration.version == SmaBatVersion.tesvolt:

            soc = self.__tcp_client.read_input_registers(1056, ModbusDataType.INT_32, unit=25) / 10
            power = self.__tcp_client.read_input_registers(1012, ModbusDataType.INT_32, unit=25) * -1
            self.peak_filter.check_values(power)
            imported, exported = self.sim_counter.sim_count(power)
        else:
            raise ValueError('Unbekannte Batterie Version')

        bat_state = BatState(
            power=power,
            soc=soc,
            imported=imported,
            exported=exported
        )
        self.store.set(bat_state)

    def set_power_limit(self, power_limit: Optional[int]) -> None:
        unit = self.component_config.configuration.modbus_id

        if power_limit is None:
            if self.last_mode is not None:
                # Kein Powerlimit gefordert, externe Steuerung war aktiv, externe Steuerung deaktivieren
                self.__tcp_client.write_register(40151, 803, data_type=ModbusDataType.UINT_32, unit=unit)
                self.__tcp_client.write_register(40149, 0, data_type=ModbusDataType.INT_32, unit=unit)
                log.debug("Keine Batteriesteuerung gefordert, deaktiviere externe Steuerung.")
                self.last_mode = None
        else:
            # Powerlimit gefordert, externe Steuerung aktivieren, Limit setzen
            self.__tcp_client.write_register(40151, 802, data_type=ModbusDataType.UINT_32, unit=unit)
            power_value = int(power_limit) * -1
            self.__tcp_client.write_register(40149, power_value, data_type=ModbusDataType.INT_32, unit=unit)
            log.debug(f"Aktive Batteriesteuerung vorhanden. Setze externe Steuerung. Leistung: {power_value}")
            self.last_mode = 'limited'

    def power_limit_controllable(self) -> bool:
        return self.component_config.configuration.version in (
            SmaBatVersion.hybrid,
            SmaBatVersion.sbs
        )


component_descriptor = ComponentDescriptor(configuration_factory=SmaSunnyBoyBatSetup)
