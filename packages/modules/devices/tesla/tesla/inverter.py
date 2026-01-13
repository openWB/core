#!/usr/bin/env python3
from modules.common.abstract_device import AbstractInverter
from modules.common.component_state import InverterState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.store import get_component_value_store
from modules.devices.tesla.tesla.http_client import PowerwallHttpClient
from modules.devices.tesla.tesla.config import TeslaInverterSetup


class TeslaInverter(AbstractInverter):
    def __init__(self, component_config: TeslaInverterSetup) -> None:
        self.component_config = component_config

    def initialize(self) -> None:
        self.store = get_component_value_store(self.component_config.type, self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))

    def update(self, client: PowerwallHttpClient, aggregate) -> None:
        pv_watt = aggregate["solar"]["instant_power"]
        if pv_watt > 5:
            pv_watt = pv_watt*-1
        self.store.set(InverterState(
            exported=aggregate["solar"]["energy_exported"],
            power=pv_watt
        ))


component_descriptor = ComponentDescriptor(configuration_factory=TeslaInverterSetup)
