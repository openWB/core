#!/usr/bin/env python3
import logging
from typing import Iterable, Union

from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_context import SingleComponentUpdateContext
from modules.common.configurable_device import ComponentFactoryByType, ConfigurableDevice, MultiComponentUpdater
from modules.devices.batterx.batterx import bat, external_inverter
from modules.devices.batterx.batterx import counter
from modules.devices.batterx.batterx import inverter
from modules.devices.batterx.batterx.config import (BatterX, BatterXBatSetup, BatterXCounterSetup,
                                                    BatterXExternalInverterSetup, BatterXInverterSetup)
from modules.common import req

log = logging.getLogger(__name__)


batterx_component_classes = Union[bat.BatterXBat, counter.BatterXCounter,
                                  inverter.BatterXInverter, external_inverter.BatterXExternalInverter]


def create_device(device_config: BatterX):
    def create_bat_component(component_config: BatterXBatSetup):
        return bat.BatterXBat(component_config=component_config,
                              device_id=device_config.id,
                              ip_address=device_config.configuration.ip_address)

    def create_counter_component(component_config: BatterXCounterSetup):
        return counter.BatterXCounter(component_config=component_config, device_id=device_config.id)

    def create_inverter_component(component_config: BatterXInverterSetup):
        return inverter.BatterXInverter(component_config=component_config, device_id=device_config.id)

    def create_external_inverter_component(component_config: BatterXExternalInverterSetup):
        return external_inverter.BatterXExternalInverter(component_config=component_config, device_id=device_config.id)

    def update_components(components: Iterable[batterx_component_classes]):
        resp_json = req.get_http_session().get(
            'http://' + device_config.configuration.ip_address + '/api.php?get=currentstate',
            timeout=5).json()
        for component in components:
            with SingleComponentUpdateContext(component.fault_state):
                component.update(resp_json)

    return ConfigurableDevice(
        device_config=device_config,
        component_factory=ComponentFactoryByType(
            bat=create_bat_component,
            counter=create_counter_component,
            inverter=create_inverter_component,
            external_inverter=create_external_inverter_component,
        ),
        component_updater=MultiComponentUpdater(update_components)
    )


device_descriptor = DeviceDescriptor(configuration_factory=BatterX)
