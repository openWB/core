import logging
import time
from typing import TypedDict, Any
from modules.common.abstract_device import AbstractBat
from modules.common.component_state import BatState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.modbus import ModbusDataType, ModbusTcpClient_
from modules.common.simcount import SimCounter
from modules.common.store import get_bat_value_store
from modules.devices.alpha_ess.alpha_ess.config import AlphaEssBatSetup

log = logging.getLogger(__name__)


class KwargsDict(TypedDict):
    device_id: int
    tcp_client: ModbusTcpClient_
    modbus_id: int


class AlphaEssBat(AbstractBat):
    def __init__(self, component_config: AlphaEssBatSetup, **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.__tcp_client: ModbusTcpClient_ = self.kwargs['tcp_client']
        self.__modbus_id: int = self.kwargs['modbus_id']
        self.sim_counter = SimCounter(self.kwargs['device_id'], self.component_config.id, prefix="speicher")
        self.store = get_bat_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))

    def update(self) -> None:
        # keine Unterschiede zwischen den Versionen

        time.sleep(0.1)
        voltage = self.__tcp_client.read_holding_registers(0x0100, ModbusDataType.INT_16, unit=self.__modbus_id)
        time.sleep(0.1)
        current = self.__tcp_client.read_holding_registers(0x0101, ModbusDataType.INT_16, unit=self.__modbus_id)

        power = voltage * current * -1 / 100
        log.debug(
            "Alpha Ess Leistung[W]: %f, Speicher-Register: Spannung[V]: %f, Strom[A]: %f" %
            (power, voltage, current)
        )
        time.sleep(0.1)
        soc_reg = self.__tcp_client.read_holding_registers(0x0102, ModbusDataType.INT_16, unit=self.__modbus_id)
        soc = int(soc_reg * 0.1)

        imported, exported = self.sim_counter.sim_count(power)
        bat_state = BatState(
            power=power,
            soc=soc,
            imported=imported,
            exported=exported
        )
        self.store.set(bat_state)


component_descriptor = ComponentDescriptor(configuration_factory=AlphaEssBatSetup)
