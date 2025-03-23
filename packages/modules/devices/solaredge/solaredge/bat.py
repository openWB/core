#!/usr/bin/env python3
import logging
from typing import Dict, Union, Optional

from pymodbus.constants import Endian

from control import data
from dataclass_utils import dataclass_from_dict
from modules.common import modbus
from modules.common.abstract_device import AbstractBat
from modules.common.component_state import BatState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.modbus import ModbusDataType
from modules.common.simcount import SimCounter
from modules.common.store import get_bat_value_store
from modules.devices.solaredge.solaredge.config import SolaredgeBatSetup
import pymodbus

log = logging.getLogger(__name__)

FLOAT32_UNSUPPORTED = -0xffffff00000000000000000000000000


class SolaredgeBat(AbstractBat):
    # Define all possible registers with their data types
    REGISTERS = {
        "Battery1StateOfEnergy": (0xe184, ModbusDataType.FLOAT_32,),  # Mirror: 0xf584
        "Battery1InstantaneousPower": (0xe174, ModbusDataType.FLOAT_32,),  # Mirror: 0xf574
        "Battery1Status": (0xe186, ModbusDataType.UINT_32,),
        "Battery2StateOfEnergy": (0xe284, ModbusDataType.FLOAT_32,),
        "Battery2InstantaneousPower": (0xe274, ModbusDataType.FLOAT_32,),
        "Battery2Status": (0xe286, ModbusDataType.UINT_32,),
        "StorageControlMode": (0xe004, ModbusDataType.UINT_16,),
        "StorageChargeDischargeDefaultMode": (0xe00a, ModbusDataType.UINT_16,),
        "RemoteControlCommandMode": (0xe00d, ModbusDataType.UINT_16,),
        "RemoteControlCommandDischargeLimit": (0xe010, ModbusDataType.FLOAT_32,),
    }

    def __init__(self,
                 device_id: int,
                 component_config: Union[Dict, SolaredgeBatSetup],
                 tcp_client: modbus.ModbusTcpClient_) -> None:
        self.__device_id = device_id
        self.component_config = dataclass_from_dict(SolaredgeBatSetup, component_config)
        self.__tcp_client = tcp_client
        self.sim_counter = SimCounter(self.__device_id, self.component_config.id, prefix="speicher")
        self.store = get_bat_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))
        self.battery_index = 1  # Nach Umsetzung des PR 2236, hier entfernen und unten als battery_index ersetzen.
        self.soc_reserve = 10  # SoC-Grenze bis zu der der Speicher entladen wird. In Config aufnehmen.

    def update(self) -> None:
        self.store.set(self.read_state())

    def read_state(self) -> BatState:
        unit = self.component_config.configuration.modbus_id

        registers_to_read = [
            f"Battery{self.battery_index}InstantaneousPower",
            f"Battery{self.battery_index}StateOfEnergy",
        ]
        values = self._read_registers(registers_to_read, unit)
        power = values[f"Battery{self.battery_index}InstantaneousPower"]
        soc = values[f"Battery{self.battery_index}StateOfEnergy"]
        if power == FLOAT32_UNSUPPORTED:
            power = 0

        imported, exported = self.sim_counter.sim_count(power)

        bat_state = BatState(
            power=power,
            soc=soc,
            imported=imported,
            exported=exported
        )
        log.debug(f"Bat {self.__tcp_client.address}: {bat_state}")
        return bat_state

    def set_power_limit(self, power_limit: Optional[int]) -> None:
        unit = self.component_config.configuration.modbus_id
        PowerLimitMode = data.data.bat_all_data.data.config.power_limit_mode

        if PowerLimitMode == 'no_limit':
            """"
            Keine Speichersteuerung, andere Steuerungen zulassen (SolarEdge One, ioBroker, Node-Red etc.).
            Falls externe Steuerungen aktiv sind, sollten diese nicht beeinfusst werden.
            Daher erfolgt im Modus "Immer" der Speichersteuerung gar keine Steuerung.
            """
            return

        """
        Die Steuerung bei SolarEdge basiert auf folgenden Einstellungen:
        Zunaechst muss der Storage Control Mode gesetzt werden:
        1 - Maximize Self Consumption FW < 4.20.36
        2 - Time of Use (Steuerung durch SolarEdge Profile) FW >= 4.20.36
        4 - Remote Control (Fuer Steuerung durch openWB)
        Dann der Remote Control Command Mode und Default Mode:
        7 - Maximize self-consumption
        anschliessend das DischargLimit setzen.

        todo: Firmware Version aus Register 40044 als String(16) auslesen und gegen Version 4.20.36 pruefen.
        """
        if power_limit is None:
            # Keine Ladung mit Speichersteuerung.
            registers_to_read = [
                "StorageControlMode",
            ]
            values = self._read_registers(registers_to_read, unit)
            if values["StorageControlMode"] == 4:
                # Steuerung deaktivieren.
                log.debug("Keine Speichersteuerung gefordert, Steuerung deaktivieren.")
                values_to_write = {
                    "RemoteControlCommandDischargeLimit": 5000,
                    "StorageChargeDischargeDefaultMode": 0,
                    "RemoteControlCommandMode": 0,
                    "StorageControlMode": 2,
                }
                self._write_registers(values_to_write, unit)
            else:
                # Steuerung bereits inaktiv.
                return

        elif power_limit >= 0:
            """
            Ladung mit Speichersteuerung.
            SolarEdge entlaedt den Speicher immer nur bis zur SoC-Reserve.
            Steuerung beenden, wenn der SoC vom Speicher die SoC-Reserve unterschreitet.
            """
            registers_to_read = [
                f"Battery{self.battery_index}StateOfEnergy",
                "StorageControlMode",
                "RemoteControlCommandDischargeLimit",
            ]
            values = self._read_registers(registers_to_read, unit)
            soc = int(values[f"Battery{self.battery_index}StateOfEnergy"])
            discharge_limit = int(values["RemoteControlCommandDischargeLimit"])

            if values["StorageControlMode"] == 4:  # Speichersteuerung aktiv.
                if self.soc_reserve > soc:
                    # Speichersteuerung deaktivieren, SoC-Reserve unterschritten.
                    log.debug("Speichersteuerung deaktivieren. SoC-Reserve unterschritten.")
                    values_to_write = {
                        "RemoteControlCommandDischargeLimit": 5000,
                        "StorageChargeDischargeDefaultMode": 0,
                        "RemoteControlCommandMode": 0,
                        "StorageControlMode": 2,
                    }
                    self._write_registers(values_to_write, unit)
                elif discharge_limit not in range(int(power_limit)-10, int(power_limit)+10):
                    # DischargeLimit nur setzen, bei Abweichung von mehr als 10W.
                    log.debug(f"Speichersteuerung aktiv, Discharge-Limit {int(power_limit)}W.")
                    values_to_write = {
                        "RemoteControlCommandDischargeLimit": int(min(power_limit, 5000))
                    }
                    self._write_registers(values_to_write, unit)
            else:  # Speichersteuerung inaktiv.
                if self.soc_reserve < soc:
                    # Speichersteuerung nur aktivieren, wenn SoC ueber SoC-Reserve.
                    log.debug(f"Speichersteuerung aktivieren. Discharge-Limit: {int(power_limit)} W.")
                    values_to_write = {
                        "StorageControlMode": 4,
                        "StorageChargeDischargeDefaultMode": 7,
                        "RemoteControlCommandMode": 7,
                        "RemoteControlCommandDischargeLimit": int(min(power_limit, 5000))
                    }
                    self._write_registers(values_to_write, unit)

    def _read_registers(self, register_names: list, unit: int) -> Dict[str, Union[int, float]]:
        values = {}
        for key in register_names:
            log.debug(f"Bat raw values {self.__tcp_client.address}: {values}")
            address, data_type = self.REGISTERS[key]
            values[key] = self.__tcp_client.read_holding_registers(
                address, data_type, wordorder=Endian.Little, unit=unit
            )
        log.debug(f"Bat raw values {self.__tcp_client.address}: {values}")
        return values

    def _write_registers(self, values_to_write: Dict[str, Union[int, float]], unit: int) -> None:
        for key, value in values_to_write.items():
            address, data_type = self.REGISTERS[key]
            encoded_value = self._encode_value(value, data_type)
            self.__tcp_client.write_registers(address, encoded_value, unit=unit)
            log.debug(f"Neuer Wert {encoded_value} in Register {address} geschrieben.")

    def _encode_value(self, value: Union[int, float], data_type: ModbusDataType) -> list:
        builder = pymodbus.payload.BinaryPayloadBuilder(
                byteorder=pymodbus.constants.Endian.Big,
                wordorder=pymodbus.constants.Endian.Little
            )
        encode_methods = {
            ModbusDataType.UINT_32: builder.add_32bit_uint,
            ModbusDataType.INT_32: builder.add_32bit_int,
            ModbusDataType.UINT_16: builder.add_16bit_uint,
            ModbusDataType.INT_16: builder.add_16bit_int,
            ModbusDataType.FLOAT_32: builder.add_32bit_float,
        }

        if data_type in encode_methods:
            encode_methods[data_type](int(value))
        else:
            raise ValueError(f"Unsupported data type: {data_type}")

        return builder.to_registers()


component_descriptor = ComponentDescriptor(configuration_factory=SolaredgeBatSetup)
