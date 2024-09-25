import logging

from modules.common.configurable_device import ComponentFactoryByType, ConfigurableDevice, IndependentComponentUpdater
from modules.devices.generic.virtual.config import Virtual, VirtualCounterSetup
from modules.common.abstract_device import DeviceDescriptor
from modules.devices.generic.virtual.counter import VirtualCounter

log = logging.getLogger(__name__)


def create_device(device_config: Virtual):
    def create_counter_component(component_config: VirtualCounterSetup):
        return VirtualCounter(device_config.id, component_config)

    return ConfigurableDevice(
        device_config=device_config,
        component_factory=ComponentFactoryByType(
            counter=create_counter_component,
        ),
        component_updater=IndependentComponentUpdater(lambda component: component.update())
    )


device_descriptor = DeviceDescriptor(configuration_factory=Virtual)
