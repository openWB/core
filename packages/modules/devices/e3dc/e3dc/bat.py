#!/usr/bin/env python3
import logging
from typing import Optional, Tuple, TypedDict, Any
from modules.common import modbus
from modules.common.abstract_device import AbstractBat, SetPoint
from modules.common.component_state import BatState
from modules.common.component_type import ComponentDescriptor
from modules.common.modbus import ModbusDataType, Endian
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.store import get_component_value_store
from modules.common.simcount._simcounter import SimCounter
from modules.common.utils.peak_filter import PeakFilter
from modules.devices.e3dc.e3dc.config import E3dcBatSetup, E3dcConfiguration
from modules.devices.e3dc.e3dc.rscp_power_control import E3dcRscpBatControl
from modules.common.component_type import ComponentType

log = logging.getLogger(__name__)


def read_bat(client: modbus.ModbusTcpClient_, modbus_id: int) -> Tuple[int, int]:
    # 40082 SoC
    soc = client.read_holding_registers(40082, ModbusDataType.INT_16, unit=modbus_id)
    # 40069 Speicherleistung
    power = client.read_holding_registers(40069, ModbusDataType.INT_32, wordorder=Endian.Little, unit=modbus_id)
    return soc, power


class KwargsDict(TypedDict):
    device_id: int
    modbus_id: int
    client: modbus.ModbusTcpClient_
    device_config: E3dcConfiguration


class E3dcBat(AbstractBat):
    def __init__(self, component_config: E3dcBatSetup, **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.__device_id: int = self.kwargs['device_id']
        self.__modbus_id: int = self.kwargs['modbus_id']
        self.client: modbus.ModbusTcpClient_ = self.kwargs['client']
        self.device_config: E3dcConfiguration = self.kwargs['device_config']
        self.sim_counter = SimCounter(self.__device_id, self.component_config.id, self.component_config.type)
        self.store = get_component_value_store(self.component_config.type, self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))
        self.peak_filter = PeakFilter(ComponentType.BAT, self.component_config.id, self.fault_state)
        self.rscp_control: Optional[E3dcRscpBatControl] = None

    def update(self) -> None:
        soc, power = read_bat(self.client, self.__modbus_id)

        self.peak_filter.check_values(power)
        imported, exported = self.sim_counter.sim_count(power)
        bat_state = BatState(
            power=power,
            soc=soc,
            imported=imported,
            exported=exported
        )
        self.store.set(bat_state)

    def set_power_limit(self, setpoint: SetPoint) -> None:
        config = self.component_config.configuration
        if config.portal_username is None or config.portal_password is None or config.rscp_key is None:
            log.warning("E3DC Speicher: Keine Batteriesteuerung möglich, da keine RSCP-Zugangsdaten hinterlegt sind.")
            return

        if self.rscp_control is None:
            self.rscp_control = E3dcRscpBatControl(
                self.device_config.address, config.portal_username, config.portal_password, config.rscp_key)

        self.rscp_control.set_power_limit(setpoint.power_limit)

    def power_limit_controllable(self) -> bool:
        # Nur steuerbar, wenn RSCP-Zugangsdaten hinterlegt sind -- sonst würde die aktive
        # Speichersteuerung fälschlich mit diesem Speicher rechnen, obwohl er gar nicht gesteuert wird.
        config = self.component_config.configuration
        return (config.portal_username is not None and
                config.portal_password is not None and
                config.rscp_key is not None)


component_descriptor = ComponentDescriptor(configuration_factory=E3dcBatSetup)
