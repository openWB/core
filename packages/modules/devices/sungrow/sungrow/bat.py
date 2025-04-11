#!/usr/bin/env python3
import logging
from typing import Any, Optional, TypedDict

from modules.common.abstract_device import AbstractBat
from modules.common.component_state import BatState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.modbus import ModbusDataType, Endian, ModbusTcpClient_
from modules.common.simcount import SimCounter
from modules.common.store import get_bat_value_store
from modules.devices.sungrow.sungrow.config import SungrowBatSetup, Sungrow
from modules.devices.sungrow.sungrow.version import Version
from modules.devices.sungrow.sungrow.firmware import Firmware

log = logging.getLogger(__name__)


class KwargsDict(TypedDict):
    client: ModbusTcpClient_
    device_config: Sungrow


class SungrowBat(AbstractBat):
    def __init__(self, component_config: SungrowBatSetup, **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.device_config: Sungrow = self.kwargs['device_config']
        self.__tcp_client: ModbusTcpClient_ = self.kwargs['client']
        self.sim_counter = SimCounter(self.device_config.id, self.component_config.id, prefix="speicher")
        self.store = get_bat_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))
        self.last_mode = 'Undefined'

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

    def set_power_limit(self, power_limit: Optional[int]) -> None:
        unit = self.device_config.configuration.modbus_id
        log.debug(f'last_mode: {self.last_mode}')

        if power_limit is None:
            log.debug("Keine Batteriesteuerung, Selbstregelung durch Wechselrichter")
            if self.last_mode is not None:
                self.__tcp_client.write_registers(13049, [0], data_type=ModbusDataType.UINT_16, unit=unit)
                self.__tcp_client.write_registers(13050, [0xCC], data_type=ModbusDataType.UINT_16, unit=unit)
                self.last_mode = None
        elif power_limit == 0:
            log.debug("Aktive Batteriesteuerung. Batterie wird auf Stop gesetzt und nicht entladen")
            if self.last_mode != 'stop':
                self.__tcp_client.write_registers(13049, [2], data_type=ModbusDataType.UINT_16, unit=unit)
                self.__tcp_client.write_registers(13050, [0xCC], data_type=ModbusDataType.UINT_16, unit=unit)
                self.last_mode = 'stop'
        elif power_limit > 0:
            log.debug(f"Aktive Batteriesteuerung. Batterie wird mit {power_limit} W entladen für den Hausverbrauch")
            if self.last_mode != 'discharge':
                self.__tcp_client.write_registers(13049, [2], data_type=ModbusDataType.UINT_16, unit=unit)
                self.__tcp_client.write_registers(13050, [0xBB], data_type=ModbusDataType.UINT_16, unit=unit)
                self.last_mode = 'discharge'
            # Die maximale Entladeleistung begrenzen auf 5000W, maximaler Wertebereich Modbusregister.
            power_value = int(min(power_limit, 5000))
            self.__tcp_client.write_registers(13051, [power_value], data_type=ModbusDataType.UINT_16, unit=unit)

    def power_limit_controllable(self) -> bool:
        return True


component_descriptor = ComponentDescriptor(configuration_factory=SungrowBatSetup)
