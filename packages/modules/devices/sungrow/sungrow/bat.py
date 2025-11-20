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
from modules.devices.sungrow.sungrow.registers import RegMode

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
        self.register_check = self.detect_register_check()

    def detect_register_check(self) -> RegMode:
        # Battery register availability test
        unit = self.device_config.configuration.modbus_id

        try:
            self.__tcp_client.read_input_registers(5213, ModbusDataType.INT_32,
                                                   wordorder=Endian.Little, device_id=unit)
            self.__tcp_client.read_input_registers(5630, ModbusDataType.INT_16, device_id=unit)
            log.debug("Battery register check: using new_registers (5213/5630).")
            return RegMode.NEW_REGISTERS
        except Exception:
            pass
        # register 13000 is always available, if unused it contains zero
        # register type can only be determined if battery power is not zero
        if self.__tcp_client.read_input_registers(13021, ModbusDataType.UINT_16, device_id=unit) == 0:
            raise ValueError("Speicherleistung aktuell 0kW. Registertyp wird gesetzt sobald "
                             "Speicher Leistungswerte liefert.")
        try:
            if self.__tcp_client.read_input_registers(13000, ModbusDataType.UINT_16, device_id=unit) != 0:
                # if battery power is not zero and register 13000 shows status bits, old registers are used
                log.debug("Battery register check: using old_registers (13021 + 13000 bits for sign).")
                return RegMode.OLD_REGISTERS
        except Exception:
            pass

        log.debug("Battery register check: using fallback (13021 + total vs PV power).")
        return RegMode.FALLBACK

    def update(self) -> None:
        unit = self.device_config.configuration.modbus_id
        soc = int(self.__tcp_client.read_input_registers(13022, ModbusDataType.UINT_16, device_id=unit) / 10)

        # === Mode 1: new_registers ===
        if self.register_check == RegMode.NEW_REGISTERS:
            bat_current = self.__tcp_client.read_input_registers(5630, ModbusDataType.INT_16, device_id=unit) * -0.1
            bat_power = self.__tcp_client.read_input_registers(5213, ModbusDataType.INT_32,
                                                               wordorder=Endian.Little, device_id=unit) * -1

        # === Mode 2: old_registers ===
        elif self.register_check == RegMode.OLD_REGISTERS:
            bat_current = self.__tcp_client.read_input_registers(13020, ModbusDataType.INT_16, device_id=unit) * -0.1
            bat_power = self.__tcp_client.read_input_registers(13021, ModbusDataType.UINT_16, device_id=unit)

            resp = self.__tcp_client._delegate.read_input_registers(13000, 1, device_id=unit)
            running_state = resp.registers[0]
            is_charging = (running_state & 0x02) != 0
            is_discharging = (running_state & 0x04) != 0

            if is_discharging:
                bat_power = -abs(bat_power)
            elif is_charging:
                bat_power = abs(bat_power)

        # === Mode 3: fallback ===
        else:
            bat_current = self.__tcp_client.read_input_registers(13020, ModbusDataType.INT_16, device_id=unit) * -0.1
            bat_power = self.__tcp_client.read_input_registers(13021, ModbusDataType.UINT_16, device_id=unit)

            total_power = self.__tcp_client.read_input_registers(13033, ModbusDataType.INT_32,
                                                                 wordorder=Endian.Little, device_id=unit)
            pv_power = self.__tcp_client.read_input_registers(5016, ModbusDataType.UINT_32,
                                                              wordorder=Endian.Little, device_id=unit)

            if total_power > pv_power:
                bat_power = -abs(bat_power)
            else:
                bat_power = abs(bat_power)

        currents = [bat_current / 3] * 3

        imported, exported = self.sim_counter.sim_count(bat_power)
        bat_state = BatState(
            power=bat_power,
            soc=soc,
            currents=currents,
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
                self.__tcp_client.write_registers(13049, [0], data_type=ModbusDataType.UINT_16, device_id=unit)
                self.__tcp_client.write_registers(13050, [0xCC], data_type=ModbusDataType.UINT_16, device_id=unit)
                self.last_mode = None
        elif power_limit == 0:
            log.debug("Aktive Batteriesteuerung. Batterie wird auf Stop gesetzt und nicht entladen")
            if self.last_mode != 'stop':
                self.__tcp_client.write_registers(13049, [2], data_type=ModbusDataType.UINT_16, device_id=unit)
                self.__tcp_client.write_registers(13050, [0xCC], data_type=ModbusDataType.UINT_16, device_id=unit)
                self.last_mode = 'stop'
        elif power_limit < 0:
            log.debug(f"Aktive Batteriesteuerung. Batterie wird mit {power_limit} W entladen für den Hausverbrauch")
            if self.last_mode != 'discharge':
                self.__tcp_client.write_registers(13049, [2], data_type=ModbusDataType.UINT_16, device_id=unit)
                self.__tcp_client.write_registers(13050, [0xBB], data_type=ModbusDataType.UINT_16, device_id=unit)
                self.last_mode = 'discharge'
            # Die maximale Entladeleistung begrenzen auf 5000W, maximaler Wertebereich Modbusregister.
            power_value = int(min(abs(power_limit), 5000))
            log.debug(f"Aktive Batteriesteuerung. Batterie wird mit {power_value} W entladen für den Hausverbrauch")
            self.__tcp_client.write_registers(13051, [power_value], data_type=ModbusDataType.UINT_16, device_id=unit)

    def power_limit_controllable(self) -> bool:
        return True


component_descriptor = ComponentDescriptor(configuration_factory=SungrowBatSetup)
