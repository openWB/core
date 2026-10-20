from modules.common import modbus
from modules.common.abstract_device import DeviceDescriptor
from modules.common.configurable_device import (
    ConfigurableDevice, ComponentFactoryByType, IndependentComponentUpdater
)
from modules.devices.keba.keba_e10.config import KebaE10, KebaE10CounterSetup
from modules.devices.keba.keba_e10.counter import KebaE10Counter


def create_device(device_config: KebaE10):
    client = None

    def create_counter_component(component_config: KebaE10CounterSetup):
        return KebaE10Counter(
            component_config,
            client=client,
            modbus_id=device_config.configuration.modbus_id
        )

    def initializer():
        nonlocal client
        client = modbus.ModbusTcpClient_(
            device_config.configuration.ip_address,
            device_config.configuration.port
        )

    return ConfigurableDevice(
        device_config=device_config,
        initializer=initializer,
        component_factory=ComponentFactoryByType(counter=create_counter_component),
        component_updater=IndependentComponentUpdater(lambda component: component.update()),
    )


device_descriptor = DeviceDescriptor(configuration_factory=KebaE10)
