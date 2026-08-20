#!/usr/bin/env python3
import logging
from typing import Any, TypedDict

from modules.common.abstract_device import AbstractBat
from modules.common.component_state import BatState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.modbus import ModbusDataType, Endian, ModbusTcpClient_
from modules.common.simcount import SimCounter
from modules.common.store import get_component_value_store
from modules.devices.anker.solarbank_4_e5000.config import Anker, AnkerBatSetup
from modules.common.utils.peak_filter import PeakFilter
from modules.common.component_type import ComponentType
from control.bat import Set as PowerState

log = logging.getLogger(__name__)

# Rohwert der Leistungsregister / POWER_GAIN = Watt (Gerät liefert mW statt W)
POWER_GAIN = 1000


class KwargsDict(TypedDict):
    device_config: Anker
    client: ModbusTcpClient_


class AnkerBat(AbstractBat):
    def __init__(self, component_config: AnkerBatSetup, **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.device_config: Anker = self.kwargs['device_config']
        self.client: ModbusTcpClient_ = self.kwargs['client']
        self.sim_counter = SimCounter(self.device_config.id, self.component_config.id, self.component_config.type)
        self.store = get_component_value_store(self.component_config.type, self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))
        self.peak_filter = PeakFilter(ComponentType.BAT, self.component_config.id, self.fault_state)
        self.last_mode = 'Undefined'

    def update(self) -> None:
        unit = self.device_config.configuration.modbus_id

        power = self.client.read_input_registers(10008, ModbusDataType.INT_32,
                                                 wordorder=Endian.Little, unit=unit) * -1 / POWER_GAIN
        soc = self.client.read_input_registers(10014, ModbusDataType.UINT_16, unit=unit)

        self.peak_filter.check_values(power)
        imported, exported = self.sim_counter.sim_count(power)
        bat_state = BatState(
            power=power,
            soc=soc,
            imported=imported,
            exported=exported
        )
        self.store.set(bat_state)

    def set_power_limit(self, power_state: PowerState) -> None:
        unit = self.device_config.configuration.modbus_id

        if power_state.bat_setpoint is None:
            log.debug("Keine Batteriesteuerung, Selbstregelung durch Wechselrichter")
            if self.last_mode is not None:
                self.client.write_register(10064, 0, data_type=ModbusDataType.UINT_16, unit=unit)
                self.last_mode = None
        else:
            if self.last_mode != 'limited':
                self.client.write_register(10064, 3, data_type=ModbusDataType.UINT_16, unit=unit)
                self.last_mode = 'limited'

            # Berechne power value: 0 = stop, != 0 = multipliziere mit -1
            # Laut Doku ist der min Wert 100W, ggf. noch Anpassung für power_limit=0 notwendig
            # ACHTUNG: POWER_GAIN hier nur nach Symmetrie-Annahme angewendet (Leseregister sind
            # nachweislich in mW). Vor Praxiseinsatz unbedingt mit einem kleinen, unkritischen
            # Grenzwert verifizieren, dass das Schreibregister ebenfalls mW statt W erwartet -
            # sonst wird ggf. eine 1000x falsche Leistung angefordert.
            power_value = 0 if power_state.bat_setpoint == 0 else int(power_state.bat_setpoint) * -1 * POWER_GAIN
            self.client.write_register(10071, power_value, data_type=ModbusDataType.INT_32, unit=unit)
            log.debug("Aktive Batteriesteuerung angefordert, angeforderte Leistung: {power_value} W")

    def power_limit_controllable(self) -> bool:
        return True


component_descriptor = ComponentDescriptor(configuration_factory=AnkerBatSetup)
