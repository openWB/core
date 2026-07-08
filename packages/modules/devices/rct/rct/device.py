#!/usr/bin/env python3
import logging
import time
from typing import Callable

from modules.common.abstract_device import DeviceDescriptor
from modules.common.configurable_device import ConfigurableDevice, ComponentFactoryByType, IndependentComponentUpdater
from modules.devices.rct.rct import rct_lib
from modules.devices.rct.rct.bat import RctBat
from modules.devices.rct.rct.config import Rct, RctBatSetup, RctCounterSetup, RctInverterSetup
from modules.devices.rct.rct.counter import RctCounter
from modules.devices.rct.rct.inverter import RctInverter

log = logging.getLogger(__name__)


def create_device(device_config: Rct):
    def create_bat_component(component_config: RctBatSetup):
        return RctBat(component_config)

    def create_counter_component(component_config: RctCounterSetup):
        return RctCounter(component_config)

    def create_inverter_component(component_config: RctInverterSetup):
        return RctInverter(component_config)

    def update_component(update_func: Callable[[rct_lib.RCT], None]):
        try:
            rct = rct_lib.RCT(device_config.configuration.ip_address)
            if rct.connect_to_server():
                update_func(rct)
        except Exception:
            raise
        finally:
            rct.close()
            time.sleep(0.5)

    return ConfigurableDevice(
        device_config=device_config,
        component_factory=ComponentFactoryByType(
            bat=create_bat_component,
            counter=create_counter_component,
            inverter=create_inverter_component,
        ),
        component_updater=IndependentComponentUpdater(lambda component: update_component(component.update)),
    )


device_descriptor = DeviceDescriptor(configuration_factory=Rct)
