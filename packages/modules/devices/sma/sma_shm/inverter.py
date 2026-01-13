#!/usr/bin/env python3

from modules.common.component_state import InverterState
from modules.common.store import get_component_value_store
from modules.common.component_type import ComponentDescriptor
from modules.devices.sma.sma_shm.config import SmaHomeManagerInverterSetup
from modules.devices.sma.sma_shm.utils import SpeedwireComponent


def parse_datagram(sma_data: dict):
    return InverterState(
        power=-int(sma_data['psupply']),
        exported=sma_data['psupplycounter'] * 1000
    )


def create_component(component_config: SmaHomeManagerInverterSetup):
    return SpeedwireComponent(component_config, value_store_factory=get_inverter_value_store, parser=parse_datagram)


component_descriptor = ComponentDescriptor(configuration_factory=SmaHomeManagerInverterSetup)
