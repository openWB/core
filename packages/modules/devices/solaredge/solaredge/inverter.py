#!/usr/bin/env python3
from typing import TypedDict, Any

from modules.common import modbus
from modules.common.abstract_device import AbstractInverter
from modules.common.component_state import InverterState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.modbus import ModbusDataType
from modules.common.store import get_inverter_value_store
from modules.devices.solaredge.solaredge.config import SolaredgeInverterSetup
from modules.devices.solaredge.solaredge.scale import create_scaled_reader
from modules.common.simcount import SimCounter


class KwargsDict(TypedDict):
    client: modbus.ModbusTcpClient_
    device_id: int


class SolaredgeInverter(AbstractInverter):
    def __init__(self,
                 component_config: SolaredgeInverterSetup,
                 **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.__tcp_client = self.kwargs['client']
        self.store = get_inverter_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))
        self._read_scaled_int16 = create_scaled_reader(
            self.__tcp_client, self.component_config.configuration.modbus_id, ModbusDataType.INT_16
        )
        self._read_scaled_uint16 = create_scaled_reader(
            self.__tcp_client, self.component_config.configuration.modbus_id, ModbusDataType.UINT_16
        )
        self._read_scaled_uint32 = create_scaled_reader(
            self.__tcp_client, self.component_config.configuration.modbus_id, ModbusDataType.UINT_32
        )
        self.sim_counter = SimCounter(self.kwargs['device_id'], self.component_config.id, prefix="Wechselrichter")

    def update(self) -> None:
        self.store.set(self.read_state())

    def read_state(self):
        # 40083 = AC Power value (Watt)
        # 40084 = AC Power scale factor
        power = self._read_scaled_int16(40083, 1)[0] * -1

        # 40093 = AC Lifetime Energy production (Watt hours)
        # 40095 = AC Lifetime scale factor
        exported = self._read_scaled_uint32(40093, 1)[0]
        # 40072/40073/40074 = AC Phase A/B/C Current value (Amps)
        # 40075 = AC Current scale factor
        currents = self._read_scaled_uint16(40072, 3)
        # 40100 = DC Power value (Watt)
        # 40101 = DC Power scale factor
        # Wenn bei Hybrid-Systemen der Speicher aus dem Netz geladen wird, ist die DC-Leistung negativ.
        dc_power = self._read_scaled_int16(40100, 1)[0] * -1

        imported, _ = self.sim_counter.sim_count(power)

        return InverterState(
            power=power,
            exported=exported,
            currents=currents,
            dc_power=dc_power,
            imported=imported,
        )


component_descriptor = ComponentDescriptor(configuration_factory=SolaredgeInverterSetup)
