from modules.common import modbus
from modules.common.abstract_device import DeviceDescriptor
from modules.common.configurable_device import ConfigurableDevice, ComponentFactoryByType, IndependentComponentUpdater
from modules.devices.kostal.kostal_sem.counter import KostalSemCounter
from modules.devices.kostal.kostal_sem.config import KostalSem, KostalSemCounterSetup


def create_device(device_config: KostalSem):
    client = None

    def create_counter_component(component_config: KostalSemCounterSetup):
        nonlocal client
        return KostalSemCounter(component_config, client=client, modbus_id=device_config.configuration.modbus_id)

    def initializer():
        nonlocal client
        client = modbus.ModbusTcpClient_(device_config.configuration.ip_address, device_config.configuration.port)

    return ConfigurableDevice(
        device_config=device_config,
        initializer=initializer,
        component_factory=ComponentFactoryByType(counter=create_counter_component),
        component_updater=IndependentComponentUpdater(lambda component: component.update()),
    )


device_descriptor = DeviceDescriptor(configuration_factory=KostalSem)
