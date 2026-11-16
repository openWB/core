#!/usr/bin/env python3
import logging
from typing import Any, TypedDict

from modules.common import modbus
from modules.common.abstract_device import AbstractBat, SetPoint
from modules.common.component_state import BatState
from modules.common.component_type import ComponentDescriptor, ComponentType
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.modbus import ModbusDataType
from modules.common.store import get_component_value_store
from modules.common.utils.peak_filter import PeakFilter
from modules.devices.fronius.fronius_sunspec.config import FroniusSunspecBatSetup

log = logging.getLogger(__name__)

# StorCtl_Mod: Bit 0 aktiviert die Lade-, Bit 1 die Entladesteuerung. Ist ein Bit nicht gesetzt,
# regelt der Wechselrichter die jeweilige Richtung selbstständig.
STOR_CTL_MOD_CHARGE = 0b01
STOR_CTL_MOD_DISCHARGE = 0b10


def _mppt_channel_address(mppt_index: int, module_count: int) -> int:
    if mppt_index < 1 or mppt_index > module_count:
        raise ValueError(
            f"Konfigurierter MPPT-Kanal {mppt_index} existiert nicht -- Gerät meldet "
            f"{module_count} Kanäle. Bitte Konfiguration am Gerät prüfen.")
    return 40285 + (mppt_index-1) * 20  # module/1/DCW, +20 je weiterem Kanal


class KwargsDict(TypedDict):
    device_id: int
    client: modbus.ModbusTcpClient_


class FroniusSunspecBat(AbstractBat):
    def __init__(self, component_config: FroniusSunspecBatSetup, **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.__tcp_client: modbus.ModbusTcpClient_ = self.kwargs['client']
        self.store = get_component_value_store(self.component_config.type, self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))
        self.peak_filter = PeakFilter(ComponentType.BAT, self.component_config.id, self.fault_state)
        self.last_mode = 'Undefined'

        # Lade- und Entladeleistung liegen auf getrennten MPPT-Kanälen, nicht auf einem mit Vorzeichen.
        # Die Kanäle ändern sich nicht zur Laufzeit, daher nur einmal beim Start prüfen. Schlägt das fehl,
        # wird die Komponente erneut initialisiert.
        unit = 1
        config = self.component_config.configuration
        module_count = self.__tcp_client.read_holding_registers(40272, ModbusDataType.UINT_16, unit=unit)  # N
        self.charge_address = _mppt_channel_address(config.mppt_index_charge, module_count)
        self.discharge_address = _mppt_channel_address(config.mppt_index_discharge, module_count)

    def update(self) -> None:
        unit = 1

        soc_raw = self.__tcp_client.read_holding_registers(40362, ModbusDataType.UINT_16, unit=unit)  # ChaState
        soc_scale = self.__tcp_client.read_holding_registers(
            40376, ModbusDataType.INT_16, unit=unit)  # ChaState_SF
        soc = soc_raw * (10 ** soc_scale)

        power_scale = self.__tcp_client.read_holding_registers(40268, ModbusDataType.INT_16, unit=unit)  # DCW_SF
        energy_scale = self.__tcp_client.read_holding_registers(40269, ModbusDataType.INT_16, unit=unit)  # DCWH_SF

        charge_power_raw = self.__tcp_client.read_holding_registers(
            self.charge_address, ModbusDataType.UINT_16, unit=unit)  # DCW
        discharge_power_raw = self.__tcp_client.read_holding_registers(
            self.discharge_address, ModbusDataType.UINT_16, unit=unit)  # DCW
        power = (charge_power_raw - discharge_power_raw) * (10 ** power_scale)

        imported_raw = self.__tcp_client.read_holding_registers(
            self.charge_address+1, ModbusDataType.UINT_32, unit=unit)  # DCWH
        exported_raw = self.__tcp_client.read_holding_registers(
            self.discharge_address+1, ModbusDataType.UINT_32, unit=unit)  # DCWH
        imported = imported_raw * (10 ** energy_scale)
        exported = exported_raw * (10 ** energy_scale)

        imported, exported = self.peak_filter.check_values(power, imported, exported)
        bat_state = BatState(
            power=power,
            soc=soc,
            imported=imported,
            exported=exported,
        )
        self.store.set(bat_state)

    def _rate_register_value(self, power: float, unit: int) -> int:
        """Wert für die Register InWRte/OutWRte: Anteil der maximalen Ladeleistung (WChaMax) in Prozent,
        skaliert mit InOutWRte_SF."""
        max_power_raw = self.__tcp_client.read_holding_registers(40356, ModbusDataType.UINT_16, unit=unit)  # WChaMax
        max_power_scale = self.__tcp_client.read_holding_registers(
            40372, ModbusDataType.INT_16, unit=unit)  # WChaMax_SF
        rate_scale = self.__tcp_client.read_holding_registers(
            40379, ModbusDataType.INT_16, unit=unit)  # InOutWRte_SF
        max_power = max_power_raw * (10 ** max_power_scale)
        percent = min(abs(power) / max_power * 100, 100) if max_power else 0
        return round(percent / (10 ** rate_scale))

    def set_power_limit(self, setpoint: SetPoint) -> None:
        power_limit = setpoint.power_limit
        unit = 1

        if power_limit is None:
            log.debug("Keine Batteriesteuerung, Selbstregelung durch Wechselrichter")
            if self.last_mode is not None:
                self.__tcp_client.write_register(40359, 0, data_type=ModbusDataType.UINT_16, unit=unit)  # StorCtl_Mod
                self.__tcp_client.write_register(40366, 100, data_type=ModbusDataType.INT_16, unit=unit)  # OutWRte
                self.__tcp_client.write_register(40367, 100, data_type=ModbusDataType.INT_16, unit=unit)  # InWRte
                self.last_mode = None
        elif power_limit == 0:
            log.debug("Aktive Batteriesteuerung. Batterie wird auf Stop gesetzt und nicht entladen")
            if self.last_mode != 'stop':
                self.__tcp_client.write_register(
                    40359, STOR_CTL_MOD_DISCHARGE, data_type=ModbusDataType.UINT_16, unit=unit)  # StorCtl_Mod
                self.__tcp_client.write_register(40366, 0, data_type=ModbusDataType.INT_16, unit=unit)  # OutWRte
                self.last_mode = 'stop'
        elif power_limit < 0:
            if self.last_mode != 'discharge':
                self.__tcp_client.write_register(
                    40359, STOR_CTL_MOD_DISCHARGE, data_type=ModbusDataType.UINT_16, unit=unit)  # StorCtl_Mod
                self.last_mode = 'discharge'
            log.debug(f"Aktive Batteriesteuerung. Batterie wird mit {abs(power_limit)} W "
                      "entladen für den Hausverbrauch")
            self.__tcp_client.write_register(
                40366, self._rate_register_value(power_limit, unit),
                data_type=ModbusDataType.INT_16, unit=unit)  # OutWRte
        elif power_limit > 0:
            if self.last_mode != 'charge':
                self.__tcp_client.write_register(40371, 1, data_type=ModbusDataType.UINT_16, unit=unit)  # ChaGriSet
                self.__tcp_client.write_register(
                    40359, STOR_CTL_MOD_CHARGE, data_type=ModbusDataType.UINT_16, unit=unit)  # StorCtl_Mod
                self.last_mode = 'charge'
            log.debug(f"Aktive Batteriesteuerung. Batterie wird mit {power_limit} W geladen")
            self.__tcp_client.write_register(
                40367, self._rate_register_value(power_limit, unit),
                data_type=ModbusDataType.INT_16, unit=unit)  # InWRte

    def power_limit_controllable(self) -> bool:
        return True


component_descriptor = ComponentDescriptor(configuration_factory=FroniusSunspecBatSetup)
