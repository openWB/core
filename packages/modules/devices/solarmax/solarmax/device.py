#!/usr/bin/env python3
import logging
from typing import Iterable, Optional, List, Union

from helpermodules.cli import run_using_positional_cli_args
from modules.common import modbus
from modules.common.abstract_device import DeviceDescriptor
from modules.common.configurable_device import ComponentFactoryByType, ConfigurableDevice, MultiComponentUpdater
from modules.devices.solarmax.solarmax import inverter
from modules.devices.solarmax.solarmax.bat import SolarmaxBat
from modules.devices.solarmax.solarmax.config import (
    Solarmax, SolarmaxBatSetup, SolarmaxConfiguration, SolarmaxInverterSetup)

log = logging.getLogger(__name__)


def create_device(device_config: Solarmax):
    client = None

    def create_bat_component(component_config: SolarmaxBatSetup):
        nonlocal client
        return SolarmaxBat(component_config, device_id=device_config.id, client=client)

    def create_inverter_component(component_config: SolarmaxInverterSetup):
        nonlocal client
        return inverter.SolarmaxInverter(component_config, device_id=device_config.id, client=client)

    def update_components(components: Iterable[Union[SolarmaxBat, inverter.SolarmaxInverter]]):
        nonlocal client
        with client:
            for component in components:
                component.update()

    def initializer():
        nonlocal client
        client = modbus.ModbusTcpClient_(device_config.configuration.ip_address, device_config.configuration.port)

    return ConfigurableDevice(
        device_config=device_config,
        initializer=initializer,
        component_factory=ComponentFactoryByType(
            bat=create_bat_component,
            inverter=create_inverter_component,
        ),
        component_updater=MultiComponentUpdater(update_components)
    )


COMPONENT_TYPE_TO_MODULE = {
    "inverter": inverter
}


def read_legacy(component_type: str, ip_address: str, num: Optional[int] = None) -> None:
    dev = create_device(Solarmax(configuration=SolarmaxConfiguration(ip_address=ip_address)))
    if component_type in COMPONENT_TYPE_TO_MODULE:
        component_config = COMPONENT_TYPE_TO_MODULE[component_type].component_descriptor.configuration_factory()
    else:
        raise Exception(
            "illegal component type " + component_type + ". Allowed values: " +
            ','.join(COMPONENT_TYPE_TO_MODULE.keys())
        )
    component_config.id = num
    dev.add_component(component_config)

    log.debug('Solarmax IP-Adresse: ' + ip_address)

    dev.update()


def main(argv: List[str]):
    run_using_positional_cli_args(read_legacy, argv)


device_descriptor = DeviceDescriptor(configuration_factory=Solarmax)
