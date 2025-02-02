#!/usr/bin/env python3
import logging
from typing import Dict, Union, Tuple

from dataclass_utils import dataclass_from_dict
from modules.common.abstract_device import AbstractBat
from modules.common.component_state import BatState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.modbus import ModbusTcpClient_, ModbusDataType
from modules.common.simcount import SimCounter
from modules.common.store import get_bat_value_store
from modules.devices.sma.sma_sunny_boy.config import SmaSunnyBoySmartEnergyBatSetup

log = logging.getLogger(__name__)


class SunnyBoySmartEnergyBat(AbstractBat):
    SMA_UINT32_NAN = 0xFFFFFFFF  # SMA uses this value to represent NaN
    SMA_UINT_64_NAN = 0xFFFFFFFFFFFFFFFF  # SMA uses this value to represent NaN

    def __init__(self,
                 device_id: int,
                 component_config: Union[Dict, SmaSunnyBoySmartEnergyBatSetup],
                 tcp_client: ModbusTcpClient_) -> None:
        self.__device_id = device_id
        self.component_config = dataclass_from_dict(SmaSunnyBoySmartEnergyBatSetup, component_config)
        self.__tcp_client = tcp_client
        self.sim_counter = SimCounter(self.__device_id, self.component_config.id, prefix="speicher")
        self.store = get_bat_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))

    def update(self) -> None:
        self.store.set(self.read())

    def read(self) -> BatState:
        unit = self.component_config.configuration.modbus_id

        # Define the required registers
        registers = {
            "Battery_SoC": (30845, ModbusDataType.UINT_32),
            "Battery_ChargePower": (31393, ModbusDataType.INT_32),
            "Battery_DischargePower": (31395, ModbusDataType.INT_32),
            "Battery_ChargedEnergy": (31401, ModbusDataType.UINT_64),
            "Battery_DischargedEnergy": (31397, ModbusDataType.UINT_64),
            "Inverter_Type": (30053, ModbusDataType.UINT_32)
        }

        # Read all values
        values = self.read_registers(registers, unit)

        if values["Battery_SoC"] == self.SMA_UINT32_NAN:
            # If the storage is empty and nothing is produced on the DC side, the inverter does not supply any values.
            values["Battery_SoC"] = 0
            power = 0
        else:
            if values["Battery_ChargePower"] > 5:
                power = values["Battery_ChargePower"]
            else:
                power = values["Battery_DischargePower"] * -1

        if (values["Battery_ChargedEnergy"] == self.SMA_UINT_64_NAN or
                values["Battery_DischargedEnergy"] == self.SMA_UINT_64_NAN):
            raise ValueError(
                f'Batterie lieferte nicht plausible Werte. Geladene Energie: {values["Battery_ChargedEnergy"]}, '
                f'Entladene Energie: {values["Battery_DischargedEnergy"]}. ',
                'Sobald die Batterie geladen/entladen wird sollte sich dieser Wert ändern, ',
                'andernfalls kann ein Defekt vorliegen.'
            )

        bat_state = BatState(
            power=power,
            soc=values["Battery_SoC"],
            exported=values["Battery_ChargedEnergy"],
            imported=values["Battery_DischargedEnergy"]
        )
        log.debug("Bat {}: {}".format(self.__tcp_client.address, bat_state))
        return bat_state

    def read_registers(
        self, registers: Dict[str, Tuple[int, ModbusDataType]], unit: int
    ) -> Dict[str, Union[int, float]]:
        values = {}
        for key, (address, data_type) in registers.items():
            values[key] = self.__tcp_client.read_holding_registers(address, data_type, unit=unit)
        log.debug("Bat raw values {}: {}".format(self.__tcp_client.address, values))
        return values


component_descriptor = ComponentDescriptor(configuration_factory=SmaSunnyBoySmartEnergyBatSetup)
