#!/usr/bin/env python3
import logging
from typing import Iterable, Optional, List, Union

from helpermodules.cli import run_using_positional_cli_args
from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_context import SingleComponentUpdateContext
from modules.common.configurable_device import ConfigurableDevice, ComponentFactoryByType, MultiComponentUpdater
from modules.common.modbus import ModbusTcpClient_
from modules.devices.deye.deye.bat import DeyeBat
from modules.devices.deye.deye.counter import DeyeCounter
from modules.devices.deye.deye.inverter import DeyeInverter
from modules.devices.deye.deye import bat, counter, inverter
from modules.devices.deye.deye.config import Deye, DeyeBatSetup, DeyeConfiguration, DeyeCounterSetup, DeyeInverterSetup

log = logging.getLogger(__name__)


def create_device(device_config: Deye):
    def create_bat_component(component_config: DeyeBatSetup):
        return DeyeBat(device_config.id, component_config, client)

    def create_counter_component(component_config: DeyeCounterSetup):
        return DeyeCounter(device_config.id, component_config, client)

    def create_inverter_component(component_config: DeyeInverterSetup):
        return DeyeInverter(device_config.id, component_config, client)

    def update_components(components: Iterable[Union[DeyeBat, DeyeCounter, DeyeInverter]]):
        with client:
            for component in components:
                with SingleComponentUpdateContext(component.fault_state):
                    component.update()

    try:
        client = ModbusTcpClient_(device_config.configuration.ip_address, device_config.configuration.port)
    except Exception:
        log.exception("Fehler in create_device")
    return ConfigurableDevice(
        device_config=device_config,
        component_factory=ComponentFactoryByType(
            bat=create_bat_component,
            counter=create_counter_component,
            inverter=create_inverter_component,
        ),
        component_updater=MultiComponentUpdater(update_components)
    )


COMPONENT_TYPE_TO_MODULE = {
    "bat": bat,
    "counter": counter,
    "inverter": inverter
}


def read_legacy(component_type: str, ip_address: str, port: int, modbus_id: int, num: Optional[int] = None) -> None:
    device_config = Deye(configuration=DeyeConfiguration(
        port=port, ip_address=ip_address))

    dev = create_device(device_config)
    if component_type in COMPONENT_TYPE_TO_MODULE:
        component_config = COMPONENT_TYPE_TO_MODULE[component_type].component_descriptor.configuration_factory()
    else:
        raise Exception(
            "illegal component type " + component_type + ". Allowed values: " +
            ','.join(COMPONENT_TYPE_TO_MODULE.keys())
        )
    component_config.configuration.modbus_id = modbus_id
    component_config.id = num
    dev.add_component(component_config)

    log.debug('Deye Port: ' + str(port))
    log.debug('Deye ID: ' + str(modbus_id))
    log.debug('Deye IP-Adresse: ' + ip_address)

    dev.update()


def main(argv: List[str]):
    run_using_positional_cli_args(read_legacy, argv)


device_descriptor = DeviceDescriptor(configuration_factory=Deye)
