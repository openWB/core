import logging
from pathlib import Path
from typing import Iterable

from helpermodules.utils.run_command import run_command
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
        return inverter.PvKit(component_config, device_id=device_config.id, client=client)

    def update_components(components: Iterable[inverter.PvKit]):
        nonlocal client
        with client:
            for component in components:
                with SingleComponentUpdateContext(component.fault_state):
                    component.update()

    def initializer():
        nonlocal client
        client = modbus.ModbusTcpClient_("192.168.193.13", 8899)

    def error_handler():
        run_command([f"{Path(__file__).resolve().parents[4]}/modules/common/restart_protoss_admin",
                     "192.168.193.13"])

    return ConfigurableDevice(
        device_config=device_config,
        initializer=initializer,
        error_handler=error_handler,
        component_factory=ComponentFactoryByType(
            inverter=create_inverter_component,
        ),
        component_updater=MultiComponentUpdater(update_components)
    )


device_descriptor = DeviceDescriptor(configuration_factory=PvKitSetup)
