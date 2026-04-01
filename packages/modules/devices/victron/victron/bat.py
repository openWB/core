#!/usr/bin/env python3
import logging
from typing import Any, Optional, TypedDict

from modules.common import modbus
from modules.common.abstract_device import AbstractBat
from modules.common.component_state import BatState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.modbus import ModbusDataType
from modules.common.simcount import SimCounter
from modules.common.store import get_bat_value_store
from modules.devices.victron.victron.config import VictronBatSetup
from modules.common.utils.peak_filter import PeakFilter
from modules.common.component_type import ComponentType
from control import data

log = logging.getLogger(__name__)


class KwargsDict(TypedDict):
    device_id: int
    client: modbus.ModbusTcpClient_


class VictronBat(AbstractBat):
    def __init__(self, component_config: VictronBatSetup, **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.__device_id: int = self.kwargs['device_id']
        self.__tcp_client: modbus.ModbusTcpClient_ = self.kwargs['client']
        self.sim_counter = SimCounter(self.__device_id, self.component_config.id, prefix="speicher")
        self.store = get_bat_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))
        self.last_mode = 'Undefined'
        self.peak_filter = PeakFilter(ComponentType.BAT, self.component_config.id, self.fault_state)
        self.current_power = 0

    def update(self) -> None:
        modbus_id = self.component_config.configuration.modbus_id
        with self.__tcp_client:
            power = self.__tcp_client.read_holding_registers(842, ModbusDataType.INT_16, unit=modbus_id)
            soc = self.__tcp_client.read_holding_registers(843, ModbusDataType.UINT_16, unit=modbus_id)
        self.peak_filter.check_values(power)
        imported, exported = self.sim_counter.sim_count(power)
        bat_state = BatState(
            power=power,
            soc=soc,
            imported=imported,
            exported=exported
        )
        self.store.set(bat_state)
        self.current_power = power

    def set_power_limit(self, power_limit: Optional[int]) -> None:
        modbus_id = self.component_config.configuration.modbus_id
        # Wenn Victron Dynamic ESS aktiv, erfolgt keine weitere Regelung in openWB
        dynamic_ess_mode = self.__tcp_client.read_holding_registers(5400, ModbusDataType.UINT_16, unit=modbus_id)
        if dynamic_ess_mode == 1:
            log.debug("Dynamic ESS Mode ist aktiv, daher erfolgt keine Regelung des Speichers durch openWB")
            return

        if power_limit is None:
            log.debug("Keine Batteriesteuerung, Selbstregelung durch Wechselrichter")
            if self.last_mode is not None:
                # ESS Mode 2 und Leistung EVU auf 0kW setzen für Selbstregelung
                self.__tcp_client.write_register(2902, 2, data_type=ModbusDataType.UINT_16, unit=modbus_id)
                self.__tcp_client.write_register(2702, 100, data_type=ModbusDataType.UINT_16, unit=modbus_id)
                self.__tcp_client.write_register(2716, 0, data_type=ModbusDataType.INT_32, unit=modbus_id)
                self.last_mode = None
        elif power_limit == 0:
            log.debug("Aktive Batteriesteuerung. Batterie wird auf Stop gesetzt und nicht entladen")
            if self.last_mode != 'stop':
                # ESS Mode 2 und Discharge Power 0% für externe Steuerung und keine Entladung
                # Leistung an EVU-Punkt auf 0kW setzen -> Eigenregelung bei laden und Entladen verhindern
                self.__tcp_client.write_register(2902, 2, data_type=ModbusDataType.UINT_16, unit=modbus_id)
                self.__tcp_client.write_register(2702, 0, data_type=ModbusDataType.UINT_16, unit=modbus_id)
                self.__tcp_client.write_register(2716, 0, data_type=ModbusDataType.INT_32, unit=modbus_id)
                self.last_mode = 'stop'
        elif power_limit < 0:
            evu_power = data.data.counter_all_data.get_evu_counter().data.get.power
            set_power = (power_limit - self.current_power) + evu_power
            log.debug(f"Aktive Batteriesteuerung Victron:"
                      f"Speicher soll mit {power_limit} W entladen werden. \n"
                      f"Aktuelle Speicherleistung: {self.current_power} W, EVU-Leistung: {evu_power} W "
                      f"EVU-Leistung um {power_limit - self.current_power} W anpassen auf {set_power} W")
            if self.last_mode != 'discharge':
                self.__tcp_client.write_register(2902, 2, data_type=ModbusDataType.UINT_16, unit=modbus_id)
                self.__tcp_client.write_register(2702, 100, data_type=ModbusDataType.UINT_16, unit=modbus_id)
                self.last_mode = 'discharge'

            # Setzen der angestrebten EVU-Leistung, Speicher versucht seine Leistung
            # anzupassen um den Zielwert zu erreichen
            self.__tcp_client.write_register(
                2716, set_power, data_type=ModbusDataType.INT_32, unit=modbus_id)
        elif power_limit > 0:
            evu_power = data.data.counter_all_data.get_evu_counter().data.get.power
            set_power = (power_limit - self.current_power) + evu_power
            log.debug(f"Aktive Batteriesteuerung Victron:"
                      f"Speicher soll mit {power_limit} W geladen werden. \n"
                      f"Aktuelle Speicherleistung: {self.current_power} W, EVU-Leistung: {evu_power} W "
                      f"EVU-Leistung um {power_limit - self.current_power} W anpassen auf {set_power} W")
            if self.last_mode != 'charge':
                self.__tcp_client.write_register(2902, 2, data_type=ModbusDataType.UINT_16, unit=modbus_id)
                self.__tcp_client.write_register(2702, 100, data_type=ModbusDataType.UINT_16, unit=modbus_id)
                self.last_mode = 'charge'
            self.__tcp_client.write_register(
                2716, set_power, data_type=ModbusDataType.INT_32, unit=modbus_id)

    def power_limit_controllable(self) -> bool:
        return True


component_descriptor = ComponentDescriptor(configuration_factory=VictronBatSetup)
