#!/usr/bin/env python3
from typing import Any, TypedDict

from modules.common.abstract_device import AbstractCounter
from modules.common.component_state import CounterState
from modules.common.component_type import ComponentDescriptor, ComponentType
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.modbus import ModbusTcpClient_
from modules.common.store import get_component_value_store
from modules.common.sunspec import points
from modules.common.sunspec.discovery import discover_models, require_model
from modules.common.sunspec.reader import read_point
from modules.common.utils.peak_filter import PeakFilter
from modules.devices.generic.sunspec.config import SunspecCounterSetup


class KwargsDict(TypedDict):
    device_id: int
    client: ModbusTcpClient_


class SunspecCounter(AbstractCounter):
    def __init__(self, component_config: SunspecCounterSetup, **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.client: ModbusTcpClient_ = self.kwargs['client']
        self.store = get_component_value_store(self.component_config.type, self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))
        self.peak_filter = PeakFilter(ComponentType.COUNTER, self.component_config.id, self.fault_state)

        unit = self.component_config.configuration.modbus_id
        models = discover_models(self.client, unit=unit)
        self.model = require_model(
            models, points.METER_FLOAT_MODELS + points.METER_INT_SF_MODELS, "SunSpec Zähler")
        self.points = (points.METER_FLOAT if self.model.model_id in points.METER_FLOAT_MODELS
                       else points.METER_INT_SF)

    def update(self) -> None:
        unit = self.component_config.configuration.modbus_id

        def read(name: str):
            return read_point(self.client, self.model, self.points[name], unit=unit)

        power = read("W")
        imported = read("TotWhImp")
        exported = read("TotWhExp")
        powers = [read("WphA"), read("WphB"), read("WphC")]
        currents = [read("AphA"), read("AphB"), read("AphC")]
        voltages = [read("PhVphA"), read("PhVphB"), read("PhVphC")]
        power_factors = [read("PFphA"), read("PFphB"), read("PFphC")]
        frequency = read("Hz")

        imported, exported = self.peak_filter.check_values(power, imported, exported)
        counter_state = CounterState(
            power=power,
            imported=imported,
            exported=exported,
            powers=powers,
            currents=currents,
            voltages=voltages,
            power_factors=power_factors,
            frequency=frequency,
        )
        self.store.set(counter_state)


component_descriptor = ComponentDescriptor(configuration_factory=SunspecCounterSetup)
