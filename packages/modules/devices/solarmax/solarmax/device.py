#!/usr/bin/env python3
import logging
from typing import Iterable, Optional, List, Union

from helpermodules.cli import run_using_positional_cli_args
from modules.common import modbus
from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_context import SingleComponentUpdateContext
from modules.common.configurable_device import ComponentFactoryByType, ConfigurableDevice, MultiComponentUpdater
from modules.devices.solarmax.solarmax import inverter
from modules.devices.solarmax.solarmax.inverter import SolarmaxInverter
from modules.devices.solarmax.solarmax.bat import SolarmaxBat
from modules.devices.solarmax.solarmax.counter_maxstorage import SolarmaxMsCounter
from modules.devices.solarmax.solarmax.inverter_maxstorage import SolarmaxMsInverter
from modules.devices.solarmax.solarmax.config import (Solarmax, SolarmaxConfiguration,
                                                      SolarmaxBatSetup, SolarmaxMsCounterSetup,
                                                      SolarmaxInverterSetup, SolarmaxMsInverterSetup)

log = logging.getLogger(__name__)


def create_device(device_config: Solarmax):
    client = None

    def create_bat_component(component_config: SolarmaxBatSetup):
        nonlocal client
        return SolarmaxBat(component_config, device_id=device_config.id, client=client)

    def create_inverter_component(component_config: SolarmaxInverterSetup):
        nonlocal client
        return SolarmaxInverter(component_config, device_id=device_config.id, client=client)

    def create_inverter_ms_component(component_config: SolarmaxMsInverterSetup):
        nonlocal client
        return SolarmaxMsInverter(component_config, device_id=device_config.id, client=client)

    def create_counter_ms_component(component_config: SolarmaxMsCounterSetup):
        nonlocal client
        return SolarmaxMsCounter(component_config, device_id=device_config.id, client=client)

    def update_components(components: Iterable[Union[SolarmaxBat, SolarmaxInverter,
                                                     SolarmaxMsCounter, SolarmaxMsInverter]]):
        nonlocal client
        with client:
            for component in components:
                with SingleComponentUpdateContext(component.fault_state):
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
            counter_maxstorage=create_counter_ms_component,
            inverter_maxstorage=create_inverter_ms_component,

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
