#!/usr/bin/env python3
import logging
from typing import Dict, Iterable, Optional, Union

from modules.common.abstract_device import DeviceDescriptor
from modules.common.configurable_device import ComponentFactoryByType, ConfigurableDevice, MultiComponentUpdater
from modules.common import req
from modules.devices.solar_watt.solar_watt.bat import SolarWattBat
from modules.devices.solar_watt.solar_watt.counter import SolarWattCounter
from modules.devices.solar_watt.solar_watt.config import (SolarWatt, SolarWattBatSetup,
                                                          SolarWattCounterSetup,
                                                          SolarWattInverterSetup)
from modules.devices.solar_watt.solar_watt.inverter import SolarWattInverter

log = logging.getLogger(__name__)


def update(components: Iterable[Union[SolarWattBat, SolarWattCounter, SolarWattInverter]],
           energy_manager: bool,
           ip_address: Optional[str] = None
           ):
    def request(url: str) -> Dict:
        response = req.get_http_session().get(url, timeout=3).json()
        if len(str(response)) < 10:
            raise ValueError("Antwort ungültig")
        return response

    energy_manager_response = None
    if energy_manager:
        energy_manager_response = request('http://'+ip_address + '/rest/kiwigrid/wizard/devices')
    else:
        gateway_response = request('http://'+ip_address+':8080/')
    for component in components:
        if isinstance(component, SolarWattInverter):
            if energy_manager_response is None:
                energy_manager_response = request('http://'+ip_address + '/rest/kiwigrid/wizard/devices')
            component.update(energy_manager_response)
        else:
            if energy_manager:
                component.update(energy_manager_response, energy_manager)
            else:
                component.update(gateway_response, energy_manager)


def create_device(device_config: SolarWatt):
    def create_bat_component(component_config: SolarWattBatSetup):
        return SolarWattBat(component_config, device_id=device_config.id)

    def create_counter_component(component_config: SolarWattCounterSetup):
        return SolarWattCounter(component_config, device_id=device_config.id)

    def create_inverter_component(component_config: SolarWattInverterSetup):
        return SolarWattInverter(component_config, device_id=device_config.id)

    def update_components(components: Dict[str, Union[SolarWattBat, SolarWattCounter, SolarWattInverter]]):
        update(components, device_config.configuration.energy_manager, device_config.configuration.ip_address)

    return ConfigurableDevice(
        device_config=device_config,
        component_factory=ComponentFactoryByType(
            bat=create_bat_component,
            counter=create_counter_component,
            inverter=create_inverter_component,
        ),
        component_updater=MultiComponentUpdater(update_components)
    )


device_descriptor = DeviceDescriptor(configuration_factory=SolarWatt)
