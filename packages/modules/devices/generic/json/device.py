#!/usr/bin/env python3
import logging
from typing import Union, Iterable

from modules.common import req
from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_context import SingleComponentUpdateContext
from modules.common.configurable_device import ConfigurableDevice, ComponentFactoryByType, MultiComponentUpdater
from modules.devices.generic.json.bat import JsonBat
from modules.devices.generic.json.config import (Json,
                                                 JsonBatSetup,
                                                 JsonCounterSetup,
                                                 JsonInverterSetup)
from modules.devices.generic.json.counter import JsonCounter
from modules.devices.generic.json.inverter import JsonInverter

log = logging.getLogger(__name__)
JsonComponent = Union[JsonBat, JsonCounter, JsonInverter]


def create_device(device_config: Json):
    def create_bat(component_config: JsonBatSetup) -> JsonBat:
        return JsonBat(component_config=component_config, device_id=device_config.id)

    def create_counter(component_config: JsonCounterSetup) -> JsonCounter:
        return JsonCounter(component_config=component_config, device_id=device_config.id)

    def create_inverter(component_config: JsonInverterSetup) -> JsonInverter:
        return JsonInverter(component_config=component_config, device_id=device_config.id)

    def update_components(components: Iterable[JsonComponent]):
        response = req.get_http_session().get(device_config.configuration.url, timeout=5).json()
        for component in components:
            with SingleComponentUpdateContext(component.fault_state):
                component.update(response)

    return ConfigurableDevice(
        device_config,
        component_factory=ComponentFactoryByType(bat=create_bat, counter=create_counter, inverter=create_inverter),
        component_updater=MultiComponentUpdater(update_components)
    )


device_descriptor = DeviceDescriptor(configuration_factory=Json)
