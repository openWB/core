#!/usr/bin/env python3
from xml.etree.ElementTree import Element

from modules.common.abstract_device import AbstractCounter
from modules.common.component_state import CounterState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.store import get_counter_value_store
from modules.devices.avm.avm.config import AvmCounterSetup


class AvmCounter(AbstractCounter):
    def __init__(self, component_config: AvmCounterSetup) -> None:
        self.component_config = component_config

    def initialize(self) -> None:
        self.store = get_counter_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))

    def update(self, deviceListElementTree: Element):
        for device in deviceListElementTree:
            name = device.find("name").text
            if name == self.component_config.configuration.name:
                presentText = device.find("present").text
                if presentText != '1':
                    continue

                powermeterBlock = device.find("powermeter")
                if powermeterBlock is not None:
                    # AVM returns mW, convert to W here
                    power = float(powermeterBlock.find("power").text)/1000
                    # AVM returns mV, convert to V here
                    voltageInfo = powermeterBlock.find("voltage")
                    if voltageInfo is not None:
                        voltages = [float(voltageInfo.text)/1000, 0, 0]
                    # AVM returns Wh
                    imported = powermeterBlock.find("energy").text

        counter_state = CounterState(
            imported=imported,
            exported=0,
            power=power,
            voltages=voltages
        )
        self.store.set(counter_state)


component_descriptor = ComponentDescriptor(configuration_factory=AvmCounterSetup)
