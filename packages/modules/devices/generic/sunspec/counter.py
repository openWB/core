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
from modules.common.sunspec.reader import read_manufacturer, read_point
from modules.common.utils.peak_filter import PeakFilter
from modules.devices.generic.sunspec.config import SunspecCounterSetup

# Fronius meters report grid power inverted vs. what openWB expects (see fronius_sunspec/counter.py).
MANUFACTURERS_WITH_INVERTED_POWER = ("fronius",)


def _replace_none(values, default: float):
    return [default if v is None else v for v in values]


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
        self.is_int_sf_model = self.model.model_id in points.METER_INT_SF_MODELS

        manufacturer = (read_manufacturer(self.client, models[points.COMMON_MODEL], unit=unit)
                        if points.COMMON_MODEL in models else "")
        self.invert_power_direction = manufacturer.lower().startswith(MANUFACTURERS_WITH_INVERTED_POWER)

    def update(self) -> None:
        unit = self.component_config.configuration.modbus_id

        def read(name: str):
            return read_point(self.client, self.model, self.points[name], unit=unit)

        sign = -1 if self.invert_power_direction else 1
        power = read("W")
        if power is None:
            raise ValueError("SunSpec Zähler liefert keinen gültigen Leistungs-Wert")
        power *= sign
        imported = read("TotWhImp")
        exported = read("TotWhExp")
        # single-/split-phase meters leave unused phases as None (sentinel) - default them so
        # CounterState doesn't see a partial [value, None, None] list.
        powers = [sign * v if v is not None else 0.0 for v in [read("WphA"), read("WphB"), read("WphC")]]
        currents = _replace_none([read("AphA"), read("AphB"), read("AphC")], 0.0)
        voltages = _replace_none([read("PhVphA"), read("PhVphB"), read("PhVphC")], 230.0)
        # int+SF models encode power factor as a percentage, float models as a ratio already (see solaredge/counter.py).
        pf_divisor = 100 if self.is_int_sf_model else 1
        power_factors = [v / pf_divisor for v in
                         _replace_none([read("PFphA"), read("PFphB"), read("PFphC")], 0.0)]
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
