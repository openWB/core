#!/usr/bin/env python3
import logging
from typing import Any, TypedDict

from modules.common import modbus
from modules.common.abstract_device import AbstractInverter
from modules.common.component_state import InverterState
from modules.common.component_type import ComponentDescriptor, ComponentType
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.modbus import ModbusDataType
from modules.common.simcount import SimCounter
from modules.common.store import get_component_value_store
from modules.common.utils.peak_filter import PeakFilter
from modules.devices.fronius.fronius_sunspec.config import FroniusSunspecInverterSetup
from modules.devices.fronius.fronius_sunspec.inv_version import FroniusInverterVersion

log = logging.getLogger(__name__)


class KwargsDict(TypedDict):
    device_id: int
    client: modbus.ModbusTcpClient_


class FroniusSunspecInverter(AbstractInverter):
    def __init__(self, component_config: FroniusSunspecInverterSetup, **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.__tcp_client: modbus.ModbusTcpClient_ = self.kwargs['client']
        self.store = get_component_value_store(self.component_config.type, self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))
        self.peak_filter = PeakFilter(ComponentType.INVERTER, self.component_config.id, self.fault_state)
        self.sim_counter = SimCounter(self.kwargs['device_id'], self.component_config.id, self.component_config.type)

    def update(self) -> None:
        unit = 1
        version = self.component_config.configuration.version

        if version == FroniusInverterVersion.mppt:
            # AC-Leistung ist bei Hybrid-Wechselrichtern bereits mit dem Speicherfluss verrechnet,
            # reine PV-Erzeugung kommt daher aus den konfigurierten DC-MPPT-Kanälen.
            module_count = self.__tcp_client.read_holding_registers(40272, ModbusDataType.UINT_16, unit=unit)  # N
            power_scale = self.__tcp_client.read_holding_registers(
                40268, ModbusDataType.INT_16, unit=unit)  # DCW_SF
            power = 0.0
            for module_index in self.component_config.configuration.pv_mppt_indices:
                if module_index < 1 or module_index > module_count:
                    raise ValueError(
                        f"Konfigurierter MPPT-Kanal {module_index} existiert nicht -- Gerät meldet "
                        f"{module_count} Kanäle. Bitte Konfiguration am Gerät prüfen.")
                address = 40285 + (module_index-1) * 20  # module/1/DCW, +20 je weiterem Kanal
                power_raw = self.__tcp_client.read_holding_registers(
                    address, ModbusDataType.UINT_16, unit=unit)  # DCW
                power += power_raw * (10 ** power_scale)
            power *= -1
        elif version == FroniusInverterVersion.ac:
            power = self.__tcp_client.read_holding_registers(40092, ModbusDataType.FLOAT_32, unit=unit) * -1  # W
        else:
            raise ValueError("Unbekannte Version "+str(version))

        exported = self.__tcp_client.read_holding_registers(40102, ModbusDataType.FLOAT_32, unit=unit)  # WH

        self.peak_filter.check_values(power)
        imported, _ = self.sim_counter.sim_count(power)

        self.store.set(InverterState(power=power, exported=exported, imported=imported))


component_descriptor = ComponentDescriptor(configuration_factory=FroniusSunspecInverterSetup)
