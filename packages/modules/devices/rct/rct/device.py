#!/usr/bin/env python3
import logging
import time
from typing import Iterable, Union

from modules.common.abstract_device import DeviceDescriptor
from modules.common.configurable_device import ConfigurableDevice, ComponentFactoryByType, MultiComponentUpdater
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

    def update_components(components: Iterable[Union[RctBat, RctCounter, RctInverter]]):
        # Zähler, Wechselrichter und Speicher teilen sich eine physische Verbindung zum RCT-Gerät - eine
        # fehlgeschlagene Verbindung muss daher für alle drei den Fehlerzustand setzen, nicht nur für die
        # Komponente, die zufällig zuerst dran war.
        rct = rct_lib.RCT(device_config.configuration.ip_address)
        try:
            rct.connect_to_server()
            for component in components:
                component.update(rct)
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
        component_updater=MultiComponentUpdater(update_components),
    )


device_descriptor = DeviceDescriptor(configuration_factory=Rct)
