import logging
import time
from typing import Iterable, Union

from modules.common import modbus
from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_context import SingleComponentUpdateContext
from modules.common.configurable_device import ComponentFactoryByType, ConfigurableDevice, MultiComponentUpdater
from modules.devices.openwb.openwb_bat_kit.bat import BatKit
from modules.devices.openwb.openwb_evu_kit.counter import EvuKit
from modules.devices.openwb.openwb_evu_kit.config import (EvuKitSetup, EvuKitBatSetup, EvuKitCounterSetup,
                                                          EvuKitInverterSetup)
from modules.devices.openwb.openwb_pv_kit.inverter import PvKit

log = logging.getLogger(__name__)


def create_device(device_config: EvuKitSetup):
    def create_bat_component(component_config: EvuKitBatSetup):
        return BatKit(device_config.id, component_config, client)

    def create_counter_component(component_config: EvuKitCounterSetup):
        return EvuKit(device_config.id, component_config, client)

    def create_inverter_component(component_config: EvuKitInverterSetup):
        return PvKit(device_config.id, component_config, client)

    def update_components(components: Iterable[Union[BatKit, EvuKit, PvKit]]):
        with client:
            for component in components:
                with SingleComponentUpdateContext(component.fault_state):
                    component.update()
                    time.sleep(0.2)

    try:
        client = modbus.ModbusTcpClient_("192.168.193.15", 8899)
    except Exception:
        log.exception("Fehler in create_device")
    return ConfigurableDevice(
        device_config=device_config,
        component_factory=ComponentFactoryByType(
            bat=create_bat_component,
            counter=create_counter_component,
            inverter=create_inverter_component,
        ),
        component_updater=MultiComponentUpdater(update_components)
    )


device_descriptor = DeviceDescriptor(configuration_factory=EvuKitSetup)
