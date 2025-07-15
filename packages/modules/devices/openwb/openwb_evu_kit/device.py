import logging
from pathlib import Path
import time
from typing import Iterable, Union

from helpermodules.utils.run_command import run_command
from modules.common import modbus
from modules.common.abstract_device import DeviceDescriptor
from modules.common.configurable_device import ComponentFactoryByType, ConfigurableDevice, MultiComponentUpdater
from modules.devices.openwb.openwb_bat_kit.bat import BatKit
from modules.devices.openwb.openwb_evu_kit.counter import EvuKit
from modules.devices.openwb.openwb_evu_kit.config import (EvuKitSetup, EvuKitBatSetup, EvuKitCounterSetup,
                                                          EvuKitInverterSetup)
from modules.devices.openwb.openwb_pv_kit.inverter import PvKit

log = logging.getLogger(__name__)


def create_device(device_config: EvuKitSetup):
    client = None

    def create_bat_component(component_config: EvuKitBatSetup):
        nonlocal client
        return BatKit(component_config, device_id=device_config.id, client=client)

    def create_counter_component(component_config: EvuKitCounterSetup):
        nonlocal client
        return EvuKit(component_config, device_id=device_config.id, client=client)

    def create_inverter_component(component_config: EvuKitInverterSetup):
        nonlocal client
        return PvKit(component_config, device_id=device_config.id, client=client)

    def update_components(components: Iterable[Union[BatKit, EvuKit, PvKit]]):
        nonlocal client
        with client:
            for component in components:
                component.update()

    def initializer():
        nonlocal client
        client = modbus.ModbusTcpClient_("192.168.193.15", 8899)

    def error_handler():
        run_command(f"{Path(__file__).resolve().parents[4]}/modules/common/restart_protoss_admin")

    return ConfigurableDevice(
        device_config=device_config,
        initializer=initializer,
        error_handler=error_handler,
        component_factory=ComponentFactoryByType(
            bat=create_bat_component,
            counter=create_counter_component,
            inverter=create_inverter_component,
        ),
        component_updater=MultiComponentUpdater(update_components)
    )


device_descriptor = DeviceDescriptor(configuration_factory=EvuKitSetup)
