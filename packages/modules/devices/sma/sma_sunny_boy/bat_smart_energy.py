#!/usr/bin/env python3
from typing import TypedDict, Any, Dict, Union, Optional
import logging

from modules.devices.sma.sma_sunny_boy.config import SmaSunnyBoySmartEnergyBatSetup
from modules.common.store import get_component_value_store
from modules.common.modbus import ModbusTcpClient_, ModbusDataType
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.component_type import ComponentDescriptor
from modules.common.component_state import BatState
from modules.common.abstract_device import AbstractBat


log = logging.getLogger(__name__)


class KwargsDict(TypedDict):
    client: ModbusTcpClient_


class SunnyBoySmartEnergyBat(AbstractBat):
    SMA_UINT32_NAN = 0xFFFFFFFF  # SMA uses this value to represent NaN
    SMA_UINT_64_NAN = 0xFFFFFFFFFFFFFFFF  # SMA uses this value to represent NaN

    # Define all possible registers with their data types
    REGISTERS = {
        "Battery_SoC": (30845, ModbusDataType.UINT_32),
        "Battery_ChargePower": (31393, ModbusDataType.INT_32),
        "Battery_DischargePower": (31395, ModbusDataType.INT_32),
        "Battery_ChargedEnergy": (31397, ModbusDataType.UINT_64),
        "Battery_DischargedEnergy": (31401, ModbusDataType.UINT_64),
        "Inverter_Type": (30053, ModbusDataType.UINT_32),
        "Externe_Steuerung": (40151, ModbusDataType.UINT_32),
        "Wirkleistungsvorgabe": (40149, ModbusDataType.UINT_32),
    }

    def __init__(self, component_config: SmaSunnyBoySmartEnergyBatSetup, **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.__tcp_client: ModbusTcpClient_ = self.kwargs['client']
        self.store = get_component_value_store(self.component_config.type, self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))
        self.last_mode = 'Undefined'
        self.inverter_type = None

    def update(self) -> None:
        self.store.set(self.read())

    def read(self) -> BatState:
        unit = self.component_config.configuration.modbus_id

        registers_to_read = [
            "Battery_SoC",
            "Battery_ChargePower",
            "Battery_DischargePower",
            "Battery_ChargedEnergy",
            "Battery_DischargedEnergy"
        ]

        if self.inverter_type is None:  # Only read Inverter_Type if not already set
            registers_to_read.append("Inverter_Type")

        values = self._read_registers(registers_to_read, unit)

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
            exported=values["Battery_DischargedEnergy"],
            imported=values["Battery_ChargedEnergy"]
        )
        if self.inverter_type is None:
            self.inverter_type = values["Inverter_Type"]
        log.debug(f"Inverter Type: {self.inverter_type}")
        log.debug(f"Bat {self.__tcp_client.address}: {bat_state}")
        return bat_state

    def set_power_limit(self, power_limit: Optional[int]) -> None:
        unit = self.component_config.configuration.modbus_id

        if power_limit is None:
            if self.last_mode is not None:
                # Kein Powerlimit gefordert, externe Steuerung war aktiv, externe Steuerung deaktivieren
                log.debug("Keine Batteriesteuerung gefordert, deaktiviere externe Steuerung.")
                values_to_write = {
                    "Externe_Steuerung": 803,
                    "Wirkleistungsvorgabe": 0,
                }
                self._write_registers(values_to_write, unit)
                self.last_mode = None
        else:
            # Powerlimit gefordert, externe Steuerung aktivieren, Limit setzen
            log.debug("Aktive Batteriesteuerung vorhanden. Setze externe Steuerung.")
            values_to_write = {
                "Externe_Steuerung": 802,
                "Wirkleistungsvorgabe": abs(power_limit)
            }
            self._write_registers(values_to_write, unit)
            self.last_mode = 'limited'

    def _read_registers(self, register_names: list, unit: int) -> Dict[str, Union[int, float]]:
        values = {}
        for key in register_names:
            address, data_type = self.REGISTERS[key]
            values[key] = self.__tcp_client.read_holding_registers(address, data_type, unit=unit)
        log.debug(f"Bat raw values {self.__tcp_client.address}: {values}")
        return values

    def _write_registers(self, values_to_write: Dict[str, Union[int, float]], unit: int) -> None:
        for key, value in values_to_write.items():
            address, data_type = self.REGISTERS[key]
            self.__tcp_client.write_register(address, value, data_type, unit=unit)
            log.debug(f"Neuer Wert {value} in Register {address} geschrieben.")

    def power_limit_controllable(self) -> bool:
        return True


component_descriptor = ComponentDescriptor(configuration_factory=SmaSunnyBoySmartEnergyBatSetup)
