#!/usr/bin/env python3
import logging
from typing import Iterable, Union

from modules.common import modbus
from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_context import SingleComponentUpdateContext
from modules.common.configurable_device import ComponentFactoryByType, ConfigurableDevice, MultiComponentUpdater
from modules.devices.powerdog.powerdog.config import Powerdog, PowerdogCounterSetup, PowerdogInverterSetup
from modules.devices.powerdog.powerdog.counter import PowerdogCounter
from modules.devices.powerdog.powerdog.inverter import PowerdogInverter

log = logging.getLogger(__name__)


def create_device(device_config: Powerdog):
    def create_counter_component(component_config: PowerdogCounterSetup):
        return PowerdogCounter(device_config.id, component_config, client, device_config.configuration.modbus_id)

    def create_inverter_component(component_config: PowerdogInverterSetup):
        return PowerdogInverter(device_config.id, component_config, client, device_config.configuration.modbus_id)

    def update_components(components: Iterable[Union[PowerdogCounter, PowerdogInverter]]):
        with client:
            if len(components) == 1:
                for component in components:
                    if isinstance(component, PowerdogInverter):
                        with SingleComponentUpdateContext(component.fault_state):
                            component.update()
                    else:
                        raise Exception(
                            "Wenn ein EVU-Zähler konfiguriert wurde, muss immer auch ein WR konfiguriert sein.")
            elif len(components) == 2:
                for component in components:
                    if isinstance(component, PowerdogInverter):
                        inverter_power = component.update()
                        break
                else:
                    inverter_power = 0
                for component in components:
                    if isinstance(component, PowerdogCounter):
                        component.update(inverter_power)
            else:
                log.warning(
                    device_config.name +
                    ": Es konnten keine Werte gelesen werden, da noch keine oder zu viele Komponenten konfiguriert "
                    + "wurden."
                )

    try:
        client = modbus.ModbusTcpClient_(device_config.configuration.ip_address, device_config.configuration.port)
    except Exception:
        log.exception("Fehler in create_device")
    return ConfigurableDevice(
        device_config=device_config,
        component_factory=ComponentFactoryByType(
            counter=create_counter_component,
            inverter=create_inverter_component,
        ),
        component_updater=MultiComponentUpdater(update_components)
    )


device_descriptor = DeviceDescriptor(configuration_factory=Powerdog)
