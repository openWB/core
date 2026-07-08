#!/usr/bin/env python3
import logging
from typing import Iterable, Union

from modules.common import req
from modules.common.abstract_device import DeviceDescriptor
from modules.common.configurable_device import ConfigurableDevice, ComponentFactoryByType, MultiComponentUpdater
from modules.devices.fems.fems import bat, counter, inverter
from modules.devices.fems.fems.config import Fems, FemsBatSetup, FemsCounterSetup, FemsInverterSetup

log = logging.getLogger(__name__)


def create_device(device_config: Fems):
    session = None

    def create_bat_component(component_config: FemsBatSetup):
        return bat.FemsBat(component_config, ip_address=device_config.configuration.ip_address, session=session)

    def create_counter_component(component_config: FemsCounterSetup):
        return counter.FemsCounter(component_config, ip_address=device_config.configuration.ip_address, session=session)

    def create_inverter_component(component_config: FemsInverterSetup):
        return inverter.FemsInverter(component_config, ip_address=device_config.configuration.ip_address,
                                     session=session)

    def update_components(components: Iterable[Union[bat.FemsBat, counter.FemsCounter, inverter.FemsInverter]]):
        for component in components:
            component.update()

    def initializer():
        nonlocal session
        session = req.get_http_session()
        session.auth = ("x", device_config.configuration.password)

    return ConfigurableDevice(
        device_config=device_config,
        initializer=initializer,
        component_factory=ComponentFactoryByType(
            bat=create_bat_component,
            counter=create_counter_component,
            inverter=create_inverter_component,
        ),
        component_updater=MultiComponentUpdater(update_components)
    )


device_descriptor = DeviceDescriptor(configuration_factory=Fems)
