#!/usr/bin/env python3
import logging
from typing import Iterable, Union

import requests

from modules.common import req
from modules.common.abstract_device import DeviceDescriptor
from modules.common.configurable_device import ComponentFactoryByType, ConfigurableDevice, MultiComponentUpdater
from modules.devices.fronius.fronius_http_api.bat import FroniusBat
from modules.devices.fronius.fronius_http_api.config import (
    Fronius, FroniusBatSetup, FroniusCounterSetup, FroniusProductionMeterSetup, FroniusInverterSetup)
from modules.devices.fronius.fronius_http_api.counter import FroniusCounter
from modules.devices.fronius.fronius_http_api.inverter import FroniusInverter
from modules.devices.fronius.fronius_http_api.inverter_production_meter import FroniusProductionMeter

log = logging.getLogger(__name__)

fronius_component_classes = Union[FroniusBat, FroniusCounter, FroniusInverter, FroniusProductionMeter]


def create_device(device_config: Fronius):
    def create_bat_component(component_config: FroniusBatSetup):
        return FroniusBat(component_config=component_config,
                          device_id=device_config.id,
                          device_config=device_config.configuration)

    def create_counter_component(component_config: FroniusCounterSetup):
        return FroniusCounter(component_config=component_config,
                              device_id=device_config.id,
                              device_config=device_config.configuration)

    def create_inverter_component(component_config: FroniusInverterSetup):
        return FroniusInverter(component_config=component_config,
                               device_id=device_config.id)

    def create_inverter_production_meter_component(component_config: FroniusProductionMeterSetup):
        return FroniusProductionMeter(component_config=component_config,
                                      device_id=device_config.id,
                                      device_config=device_config.configuration)

    def update_components(components: Iterable[fronius_component_classes]):
        powerflow_response = None
        meter_system_response = None

        def get_powerflow_response():
            nonlocal powerflow_response
            if powerflow_response is None:
                try:
                    powerflow_response = req.get_http_session().get(
                        (f'http://{device_config.configuration.ip_address}'
                            '/solar_api/v1/GetPowerFlowRealtimeData.fcgi'),
                        params=(('Scope', 'System'),),
                        timeout=5).json()
                except (requests.ConnectTimeout, requests.ConnectionError) as e:
                    # Nachtmodus: WR ist ausgeschaltet
                    powerflow_response = e
            return powerflow_response

        def get_meter_system_response():
            nonlocal meter_system_response
            if meter_system_response is None:
                meter_system_response = req.get_http_session().get(
                    (f'http://{device_config.configuration.ip_address}'
                        '/solar_api/v1/GetMeterRealtimeData.cgi'),
                    params=(('Scope', 'System'),),
                    timeout=5).json()
            return meter_system_response

        for component in components:
            component_type = component.component_config.type
            if component_type in ("inverter", "bat"):
                component.update(get_powerflow_response())
            elif component_type == "counter":
                variant = component.component_config.configuration.variant
                component.update(get_powerflow_response(),
                                 get_meter_system_response() if variant == 2 else None)
            elif component_type == "inverter_production_meter":
                variant = component.component_config.configuration.variant
                component.update(get_meter_system_response() if variant == 2 else None)

    return ConfigurableDevice(
        device_config=device_config,
        component_factory=ComponentFactoryByType(
            bat=create_bat_component,
            counter=create_counter_component,
            inverter=create_inverter_component,
            inverter_production_meter=create_inverter_production_meter_component,
        ),
        component_updater=MultiComponentUpdater(update_components)
    )


device_descriptor = DeviceDescriptor(configuration_factory=Fronius)
