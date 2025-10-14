#!/usr/bin/env python3
import logging
from typing import Iterable, Union

import requests

from modules.common import req
from modules.common.abstract_device import DeviceDescriptor
from modules.common.configurable_device import ComponentFactoryByType, ConfigurableDevice, MultiComponentUpdater
from modules.devices.fronius.fronius.bat import FroniusBat
from modules.devices.fronius.fronius.config import (Fronius, FroniusBatSetup, FroniusSecondaryInverterSetup,
                                                    FroniusSmCounterSetup, FroniusS0CounterSetup,
                                                    FroniusProductionCounterSetup, FroniusInverterSetup)
from modules.devices.fronius.fronius.counter_s0 import FroniusS0Counter
from modules.devices.fronius.fronius.counter_sm import FroniusSmCounter
from modules.devices.fronius.fronius.inverter import FroniusInverter
from modules.devices.fronius.fronius.inverter_secondary import FroniusSecondaryInverter
from modules.devices.fronius.fronius.inverter_production_counter import FroniusProductionCounter

log = logging.getLogger(__name__)

fronius_component_classes = Union[FroniusBat, FroniusSmCounter, FroniusS0Counter,
                                  FroniusInverter, FroniusSecondaryInverter, FroniusProductionCounter]


def create_device(device_config: Fronius):
    def create_bat_component(component_config: FroniusBatSetup):
        return FroniusBat(component_config=component_config,
                          device_id=device_config.id,
                          device_config=device_config.configuration)

    def create_counter_sm_component(component_config: FroniusSmCounterSetup):
        return FroniusSmCounter(component_config=component_config,
                                device_id=device_config.id,
                                device_config=device_config.configuration)

    def create_counter_s0_component(component_config: FroniusS0CounterSetup):
        return FroniusS0Counter(component_config=component_config,
                                device_id=device_config.id,
                                device_config=device_config.configuration)

    def create_inverter_component(component_config: FroniusInverterSetup):
        return FroniusInverter(component_config=component_config,
                               device_id=device_config.id)

    def create_inverter_secondary_component(component_config: FroniusSecondaryInverterSetup):
        return FroniusSecondaryInverter(component_config=component_config,
                                        device_id=device_config.id)

    def create_inverter_counter_production_component(component_config: FroniusProductionCounterSetup):
        return FroniusProductionCounter(component_config=component_config,
                                        device_id=device_config.id,
                                        device_config=device_config.configuration)

    def update_components(components: Iterable[fronius_component_classes]):
        inverter_response = None
        for component in components:
            if (
                component.component_config.type == "inverter" or
                component.component_config.type == "inverter_secondary"
            ):
                if inverter_response is None:
                    try:
                        inverter_response = req.get_http_session().get(
                            (f'http://{device_config.configuration.ip_address}'
                                '/solar_api/v1/GetPowerFlowRealtimeData.fcgi'),
                            params=(('Scope', 'System'),),
                            timeout=3).json()
                    except (requests.ConnectTimeout, requests.ConnectionError) as e:
                        inverter_response = e
                    # Nachtmodus: WR ist ausgeschaltet
                component.update(inverter_response)

        for component in components:
            if (
                component.component_config.type != "inverter" and
                component.component_config.type != "inverter_secondary"
            ):
                component.update()

    return ConfigurableDevice(
        device_config=device_config,
        component_factory=ComponentFactoryByType(
            bat=create_bat_component,
            counter_sm=create_counter_sm_component,
            counter_s0=create_counter_s0_component,
            inverter=create_inverter_component,
            inverter_secondary=create_inverter_secondary_component,
            inverter_counter_production=create_inverter_counter_production_component,
        ),
        component_updater=MultiComponentUpdater(update_components)
    )


device_descriptor = DeviceDescriptor(configuration_factory=Fronius)
