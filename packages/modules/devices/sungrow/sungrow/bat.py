#!/usr/bin/env python3
from typing import Dict, Union

from dataclass_utils import dataclass_from_dict
from modules.common import modbus
from modules.common.abstract_device import AbstractBat
from modules.common.component_state import BatState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.modbus import ModbusDataType, Endian
from modules.common.simcount import SimCounter
from modules.common.store import get_bat_value_store
from modules.devices.sungrow.sungrow.config import SungrowBatSetup, Sungrow
from modules.devices.sungrow.sungrow.version import Version
from modules.devices.sungrow.sungrow.firmware import Firmware


class SungrowBat(AbstractBat):
    def __init__(self,
                 device_config: Union[Dict, Sungrow],
                 component_config: Union[Dict, SungrowBatSetup],
                 tcp_client: modbus.ModbusTcpClient_) -> None:
        self.device_config = device_config
        self.component_config = dataclass_from_dict(SungrowBatSetup, component_config)
        self.__tcp_client = tcp_client
        self.sim_counter = SimCounter(self.device_config.id, self.component_config.id, prefix="speicher")
        self.store = get_bat_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))

    def update(self) -> None:
        unit = self.device_config.configuration.modbus_id
        soc = int(self.__tcp_client.read_input_registers(13022, ModbusDataType.UINT_16, unit=unit) / 10)

        if (
            Firmware(self.device_config.configuration.firmware) == Firmware.v2
            and self.device_config.configuration.version == Version.SH
        ):
            bat_power = self.__tcp_client.read_input_registers(13021, ModbusDataType.INT_16, unit=unit) * -1
        else:
            bat_power = self.__tcp_client.read_input_registers(13021, ModbusDataType.UINT_16, unit=unit)

            # Beim WiNet S-Dongle fehlt das Register für das Vorzeichen der Speicherleistung
            if self.device_config.configuration.version == Version.SH_winet_dongle:
                total_power = self.__tcp_client.read_input_registers(13033, ModbusDataType.INT_32,
                                                                     wordorder=Endian.Little, unit=unit)
                pv_power = self.__tcp_client.read_input_registers(5016, ModbusDataType.UINT_32,
                                                                  wordorder=Endian.Little, unit=unit)

                # Ist die Gesamtleistung des WR größer als die PV-Erzeugung wird der Speicher entladen
                if total_power > pv_power:
                    bat_power = bat_power * -1
            else:
                resp = self.__tcp_client._delegate.read_input_registers(13000, 1, unit=unit)
                binary = bin(resp.registers[0])[2:].zfill(8)
                if binary[5] == "1":
                    bat_power = bat_power * -1

        imported, exported = self.sim_counter.sim_count(bat_power)
        bat_state = BatState(
            power=bat_power,
            soc=soc,
            imported=imported,
            exported=exported
        )
        self.store.set(bat_state)


component_descriptor = ComponentDescriptor(configuration_factory=SungrowBatSetup)
