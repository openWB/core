#!/usr/bin/env python3
from typing import Any, TypedDict

from modules.common.abstract_device import AbstractBat
from modules.common.component_state import BatState
from modules.common.component_type import ComponentDescriptor, ComponentType
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.modbus import ModbusTcpClient_
from modules.common.simcount import SimCounter
from modules.common.store import get_component_value_store
from modules.common.sunspec import points
from modules.common.sunspec.discovery import discover_models, require_model
from modules.common.sunspec.reader import read_point
from modules.common.utils.peak_filter import PeakFilter
from modules.devices.generic.sunspec.config import SunspecBatSetup


class KwargsDict(TypedDict):
    device_id: int
    client: ModbusTcpClient_


class SunspecBat(AbstractBat):
    def __init__(self, component_config: SunspecBatSetup, **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.client: ModbusTcpClient_ = self.kwargs['client']
        self.store = get_component_value_store(self.component_config.type, self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))
        self.peak_filter = PeakFilter(ComponentType.BAT, self.component_config.id, self.fault_state)
        self.sim_counter = SimCounter(self.kwargs['device_id'], self.component_config.id, self.component_config.type)

        unit = self.component_config.configuration.modbus_id
        models = discover_models(self.client, unit=unit)
        self.battery_model = require_model(models, points.BATTERY_MODELS, "SunSpec Speicher")

    def update(self) -> None:
        unit = self.component_config.configuration.modbus_id

        def read(name: str):
            return read_point(self.client, self.battery_model, points.BATTERY[name], unit=unit)

        # SunSpec W ist negativ beim Laden, positiv beim Entladen - umgekehrt zur openWB-Konvention.
        power = read("W") * -1
        soc = read("SoC")

        self.peak_filter.check_values(power)
        imported, exported = self.sim_counter.sim_count(power)
        bat_state = BatState(
            power=power,
            soc=soc,
            imported=imported,
            exported=exported,
        )
        self.store.set(bat_state)


component_descriptor = ComponentDescriptor(configuration_factory=SunspecBatSetup)
