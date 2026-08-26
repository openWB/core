#!/usr/bin/env python3
import json
import logging
from typing import Iterable, Union

from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_context import SingleComponentUpdateContext
from modules.common.configurable_device import ComponentFactoryByType, ConfigurableDevice, MultiComponentUpdater
from modules.common import req
from modules.devices.solar_log.solar_log.counter import SolarLogCounter
from modules.devices.solar_log.solar_log.config import SolarLog, SolarLogCounterSetup, SolarLogInverterSetup
from modules.devices.solar_log.solar_log.inverter import SolarLogInverter

log = logging.getLogger(__name__)


def create_device(device_config: SolarLog):
    def create_counter_component(component_config: SolarLogCounterSetup):
        return SolarLogCounter(component_config, device_id=device_config.id)

    def create_inverter_component(component_config: SolarLogInverterSetup):
        return SolarLogInverter(component_config)

    def update_components(components: Iterable[Union[SolarLogCounter, SolarLogInverter]]):
        response = req.get_http_session().post('http://'+device_config.configuration.ip_address+'/getjp',
                                               data=json.dumps({"801": {"170": None}}), timeout=5).json()
        for component in components:
            with SingleComponentUpdateContext(component.fault_state):
                component.update(response)

    return ConfigurableDevice(
        device_config=device_config,
        component_factory=ComponentFactoryByType(
            counter=create_counter_component,
            inverter=create_inverter_component,
        ),
        component_updater=MultiComponentUpdater(update_components)
    )


device_descriptor = DeviceDescriptor(configuration_factory=SolarLog)
