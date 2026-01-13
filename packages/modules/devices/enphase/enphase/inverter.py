#!/usr/bin/env python3
import logging
from typing import Any, Dict

from modules.common.abstract_device import AbstractInverter
from modules.common.component_state import InverterState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.store import get_component_value_store
from modules.devices.enphase.enphase.config import EnphaseInverterSetup

log = logging.getLogger(__name__)


class EnphaseInverter(AbstractInverter):
    def __init__(self, component_config: EnphaseInverterSetup) -> None:
        self.component_config = component_config

    def initialize(self) -> None:
        self.store = get_component_value_store(self.component_config.type, self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))

    def update(self, response: Dict[str, Any], live_data) -> None:
        meter = None
        for m in response:
            if m['eid'] == int(self.component_config.configuration.eid):
                meter = m
                break
        if meter is None:
            # configuration wrong or error
            raise ValueError("Es konnten keine Daten vom Messgerät gelesen werden.")
        power = meter['activePower']
        if power >= 0:
            power = power * -1
        else:
            power = 0
        inverter_state = InverterState(
            power=power,
            exported=meter['actEnergyDlvd']
        )
        self.store.set(inverter_state)


component_descriptor = ComponentDescriptor(configuration_factory=EnphaseInverterSetup)
