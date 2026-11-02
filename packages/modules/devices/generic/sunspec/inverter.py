#!/usr/bin/env python3
from typing import Any, TypedDict

from modules.common.abstract_device import AbstractInverter
from modules.common.component_state import InverterState
from modules.common.component_type import ComponentDescriptor, ComponentType
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.modbus import ModbusTcpClient_
from modules.common.simcount import SimCounter
from modules.common.store import get_component_value_store
from modules.common.sunspec import points
from modules.common.sunspec.discovery import discover_models, require_model
from modules.common.sunspec.reader import read_point
from modules.common.utils.peak_filter import PeakFilter
from modules.devices.generic.sunspec.config import SunspecInverterSetup


class KwargsDict(TypedDict):
    device_id: int
    client: ModbusTcpClient_


class SunspecInverter(AbstractInverter):
    def __init__(self, component_config: SunspecInverterSetup, **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.client: ModbusTcpClient_ = self.kwargs['client']
        self.store = get_component_value_store(self.component_config.type, self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))
        self.peak_filter = PeakFilter(ComponentType.INVERTER, self.component_config.id, self.fault_state)
        self.sim_counter = SimCounter(self.kwargs['device_id'], self.component_config.id, self.component_config.type)

        unit = self.component_config.configuration.modbus_id
        models = discover_models(self.client, unit=unit)
        self.model = require_model(
            models, points.INVERTER_FLOAT_MODELS + points.INVERTER_INT_SF_MODELS, "SunSpec Wechselrichter")
        self.points = (points.INVERTER_FLOAT if self.model.model_id in points.INVERTER_FLOAT_MODELS
                       else points.INVERTER_INT_SF)

    def update(self) -> None:
        unit = self.component_config.configuration.modbus_id

        def read(name: str):
            return read_point(self.client, self.model, self.points[name], unit=unit)

        power = read("W") * -1
        exported = read("WH")

        _, exported = self.peak_filter.check_values(power, None, exported)
        imported, _ = self.sim_counter.sim_count(power)

        inverter_state = InverterState(
            power=power,
            exported=exported,
            imported=imported,
        )
        self.store.set(inverter_state)


component_descriptor = ComponentDescriptor(configuration_factory=SunspecInverterSetup)
