import logging
from typing import Iterable

from modules.common import modbus
from modules.common.component_context import SingleComponentUpdateContext
from modules.common.abstract_device import DeviceDescriptor
from modules.common.configurable_device import ComponentFactoryByType, ConfigurableDevice, MultiComponentUpdater
from modules.devices.openwb.openwb_bat_kit.config import BatKitSetup, BatKitBatSetup
from modules.devices.openwb.openwb_bat_kit.bat import BatKit

log = logging.getLogger(__name__)


def create_device(device_config: BatKitSetup):
    def create_bat_component(component_config: BatKitBatSetup):
        return BatKit(device_config.id, component_config, client)

    def update_components(components: Iterable[BatKit]):
        with client:
            for component in components:
                with SingleComponentUpdateContext(component.fault_state):
                    component.update()

    try:
        client = modbus.ModbusTcpClient_("192.168.193.19", 8899)
    except Exception:
        log.exception("Fehler in create_device")
    return ConfigurableDevice(
        device_config=device_config,
        component_factory=ComponentFactoryByType(
            bat=create_bat_component,
        ),
        component_updater=MultiComponentUpdater(update_components)
    )


device_descriptor = DeviceDescriptor(configuration_factory=BatKitSetup)
