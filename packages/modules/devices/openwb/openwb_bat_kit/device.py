import logging
from typing import Iterable

from modules.common import modbus
from modules.common.abstract_device import DeviceDescriptor
from modules.common.configurable_device import ComponentFactoryByType, ConfigurableDevice, MultiComponentUpdater
from modules.devices.openwb.openwb_bat_kit.config import BatKitSetup, BatKitBatSetup
from modules.devices.openwb.openwb_bat_kit.bat import BatKit

log = logging.getLogger(__name__)


def create_device(device_config: BatKitSetup):
    client = None

    def create_bat_component(component_config: BatKitBatSetup):
        nonlocal client
        return BatKit(component_config, device_id=device_config.id, client=client)

    def update_components(components: Iterable[BatKit]):
        nonlocal client
        with client:
            for component in components:
                component.update()

    def initializer():
        nonlocal client
        client = modbus.ModbusTcpClient_("192.168.193.19", 8899)

    return ConfigurableDevice(
        device_config=device_config,
        initializer=initializer,
        component_factory=ComponentFactoryByType(
            bat=create_bat_component,
        ),
        component_updater=MultiComponentUpdater(update_components)
    )


device_descriptor = DeviceDescriptor(configuration_factory=BatKitSetup)
