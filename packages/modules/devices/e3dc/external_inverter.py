#!/usr/bin/env python3
import logging

from modules.common import modbus
from modules.common.component_state import InverterState
from modules.common.component_type import ComponentDescriptor
from modules.common.modbus import ModbusDataType, Endian
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.store import get_inverter_value_store
from modules.common.simcount._simcounter import SimCounter
from modules.devices.e3dc.config import E3dcExternalInverterSetup


log = logging.getLogger(__name__)


def read_external_inverter(client: modbus.ModbusTcpClient_, modbus_id: int) -> int:
    # 40075 externe PV Leistung
    pv_external = int(client.read_holding_registers(
        40075, ModbusDataType.INT_32, wordorder=Endian.Little, unit=modbus_id))
    return pv_external


class E3dcExternalInverter:
    def __init__(self,
                 device_id: int,
                 component_config: E3dcExternalInverterSetup,
                 modbus_id: int) -> None:
        self.component_config = component_config
        self.__modbus_id = modbus_id
        self.sim_counter = SimCounter(device_id, self.component_config.id, prefix="pv")
        self.store = get_inverter_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))

    def update(self, client: modbus.ModbusTcpClient_) -> None:

        pv_external = read_external_inverter(client, self.__modbus_id)
        # pv_external - > pv Leistung
        # die als externe Produktion an e3dc angeschlossen ist
        # Im gegensatz zur Implementierung in Version 1.9 wird nicht mehr die PV
        # Leistung vom WR1 gelesen, da die durch v2.0 separat gehandelt wird
        _, pv_exported = self.sim_counter.sim_count(pv_external)
        inverter_state = InverterState(
            power=pv_external,
            exported=pv_exported
        )
        self.store.set(inverter_state)


component_descriptor = ComponentDescriptor(configuration_factory=E3dcExternalInverterSetup)
