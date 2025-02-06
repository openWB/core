import logging
from typing import Iterable

from modules.common import modbus
from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_context import SingleComponentUpdateContext
from modules.common.configurable_device import ComponentFactoryByType, ConfigurableDevice, MultiComponentUpdater
from modules.devices.openwb.openwb_pv_kit import inverter
from modules.devices.openwb.openwb_pv_kit.config import PvKitSetup, PvKitInverterSetup

log = logging.getLogger(__name__)


def create_device(device_config: PvKitSetup):
    client = None

    def create_inverter_component(component_config: PvKitInverterSetup):
        nonlocal client
        return inverter.PvKit(device_config.id, component_config, client)

    def update_components(components: Iterable[inverter.PvKit]):
        nonlocal client
        with client:
            for component in components:
                with SingleComponentUpdateContext(component.fault_state):
                    component.update()

    def initializer():
        nonlocal client
        client = modbus.ModbusTcpClient_("192.168.193.13", 8899)

    return ConfigurableDevice(
        device_config=device_config,
        initializer=initializer,
        component_factory=ComponentFactoryByType(
            inverter=create_inverter_component,
        ),
        component_updater=MultiComponentUpdater(update_components)
    )


device_descriptor = DeviceDescriptor(configuration_factory=PvKitSetup)
