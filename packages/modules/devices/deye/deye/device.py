#!/usr/bin/env python3
import logging
from typing import Iterable, Union

from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_context import SingleComponentUpdateContext
from modules.common.configurable_device import ConfigurableDevice, ComponentFactoryByType, MultiComponentUpdater
from modules.common.modbus import ModbusTcpClient_
from modules.devices.deye.deye.bat import DeyeBat
from modules.devices.deye.deye.counter import DeyeCounter
from modules.devices.deye.deye.inverter import DeyeInverter
from modules.devices.deye.deye.config import Deye, DeyeBatSetup, DeyeCounterSetup, DeyeInverterSetup

log = logging.getLogger(__name__)


def create_device(device_config: Deye):
    client = None

    def create_bat_component(component_config: DeyeBatSetup):
        return DeyeBat(component_config=component_config, device_id=device_config.id, client=client)

    def create_counter_component(component_config: DeyeCounterSetup):
        return DeyeCounter(component_config=component_config, device_id=device_config.id, client=client)

    def create_inverter_component(component_config: DeyeInverterSetup):
        return DeyeInverter(component_config=component_config, device_id=device_config.id, client=client)

    def update_components(components: Iterable[Union[DeyeBat, DeyeCounter, DeyeInverter]]):
        with client:
            for component in components:
                with SingleComponentUpdateContext(component.fault_state):
                    component.update()

    def initializer():
        nonlocal client
        client = ModbusTcpClient_(device_config.configuration.ip_address, device_config.configuration.port)

    return ConfigurableDevice(
        device_config=device_config,
        initializer=initializer,
        component_factory=ComponentFactoryByType(
            bat=create_bat_component,
            counter=create_counter_component,
            inverter=create_inverter_component,
        ),
        component_updater=MultiComponentUpdater(update_components)
    )


device_descriptor = DeviceDescriptor(
    configuration_factory=Deye,
    compatibility_device_note="Einige Versionen des LSE3 Dongles sind kompatibel. Die Auslesung über den LSW3 ist "
    "nicht möglich!\nBei Inkompatibilität kann unser Netzwerk Modbus Adapter v2 eingesetzt werden."
)
