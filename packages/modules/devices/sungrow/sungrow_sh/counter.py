#!/usr/bin/env python3
from typing import TypedDict, Any

from modules.common.abstract_device import AbstractCounter
from modules.common.component_state import CounterState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.modbus import ModbusDataType, Endian, ModbusTcpClient_
from modules.common.simcount import SimCounter
from modules.common.store import get_counter_value_store
from modules.devices.sungrow.sungrow_sh.config import SungrowSH, SungrowSHCounterSetup
from modules.devices.sungrow.sungrow_sh.version import Version


class KwargsDict(TypedDict):
    client: ModbusTcpClient_
    device_config: SungrowSH


class SungrowSHCounter(AbstractCounter):
    def __init__(self, component_config: SungrowSHCounterSetup, **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.device_config: SungrowSH = self.kwargs['device_config']
        self.__tcp_client: ModbusTcpClient_ = self.kwargs['client']
        self.sim_counter = SimCounter(self.device_config.id, self.component_config.id, prefix="evu")
        self.store = get_counter_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))
        self.fault_text = "Dieser Sungrow Zähler liefert von Werk aus (entgegen der Dokumentation) "\
            "keine Leistung der einzelnen Phasen. "\
            "Das Lastmanagement ist daher nur anhand der Gesamtleistung (nicht phasenbasiert) möglich."

    def update(self):
        unit = self.device_config.configuration.modbus_id
        power = self.__tcp_client.read_input_registers(13009, ModbusDataType.INT_32, 
                                                       wordorder=Endian.Little, unit=unit) * -1
        try:
            powers = self.__tcp_client.read_input_registers(5602, [ModbusDataType.INT_32] * 3, 
                                                            wordorder=Endian.Little, unit=unit)
        except Exception:
            powers = None
            self.fault_state.no_error(self.fault_text)
        
        frequency = self.__tcp_client.read_input_registers(5035, ModbusDataType.UINT_16, unit=unit) / 10
        if self.device_config.configuration.version == Version.SH_winet_dongle:
            # On WiNet-S, the frequency accuracy is higher by one place
            frequency /= 10

        power_factor = self.__tcp_client.read_input_registers(5034, ModbusDataType.INT_16, unit=unit) / 1000

        if self.device_config.configuration.version == Version.SH:
            # SH (LAN) provides accurate values from meter
            voltages = self.__tcp_client.read_input_registers(5740, [ModbusDataType.UINT_16] * 3,
                                                              wordorder=Endian.Little, unit=unit)
        else:
            # These are actually output voltages of the inverter:
            voltages = self.__tcp_client.read_input_registers(5018, [ModbusDataType.UINT_16] * 3,
                                                              wordorder=Endian.Little, unit=unit)

        voltages = [value / 10 for value in voltages]

        imported, exported = self.sim_counter.sim_count(power)

        counter_state = CounterState(
            imported=imported,
            exported=exported,
            power=power,
            powers=powers,
            voltages=voltages,
            frequency=frequency,
            power_factors=[power_factor] * 3
        )
        self.store.set(counter_state)


component_descriptor = ComponentDescriptor(configuration_factory=SungrowSHCounterSetup)
