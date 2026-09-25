import logging
from typing import Iterable, Union

from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_context import SingleComponentUpdateContext
from modules.common.configurable_device import ConfigurableDevice, ComponentFactoryByType, MultiComponentUpdater
from modules.common.req import get_http_session
from modules.devices.discovergy.discovergy import counter, inverter
from modules.devices.discovergy.discovergy.config import (
    Discovergy,
    DiscovergyCounterSetup,
    DiscovergyInverterSetup)

log = logging.getLogger(__name__)


def create_device(device_config: Discovergy):
    session = None

    def create_counter_component(component_config: DiscovergyCounterSetup):
        return counter.DiscovergyCounter(component_config=component_config)

    def create_inverter_component(component_config: DiscovergyInverterSetup):
        return inverter.DiscovergyInverter(component_config=component_config)

    def initializer():
        nonlocal session
        session = get_http_session()
        session.auth = (device_config.configuration.user, device_config.configuration.password)

    def update_components(components: Iterable[Union[counter.DiscovergyCounter, inverter.DiscovergyInverter]]):
        # Fehler pro Komponente isoliert, statt bei einem Fehler alle als defekt zu markieren.
        for component in components:
            with SingleComponentUpdateContext(component.fault_state):
                component.update(session)

    return ConfigurableDevice(
        device_config=device_config,
        initializer=initializer,
        component_factory=ComponentFactoryByType(counter=create_counter_component, inverter=create_inverter_component),
        component_updater=MultiComponentUpdater(update_components),
    )


device_descriptor = DeviceDescriptor(configuration_factory=Discovergy)
