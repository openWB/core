#!/usr/bin/env python3
import logging
from typing import Iterable, Union

from modules.common import modbus
from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_context import SingleComponentUpdateContext
from modules.common.configurable_device import ComponentFactoryByType, ConfigurableDevice, MultiComponentUpdater
from modules.devices.sungrow.sungrow.bat import SungrowBat
from modules.devices.sungrow.sungrow.config import Sungrow, SungrowBatSetup, SungrowCounterSetup, SungrowInverterSetup
from modules.devices.sungrow.sungrow.counter import SungrowCounter
from modules.devices.sungrow.sungrow.inverter import SungrowInverter

log = logging.getLogger(__name__)


def create_device(device_config: Sungrow):
    def create_bat_component(component_config: SungrowBatSetup):
        return SungrowBat(device_config, component_config, client)

    def create_counter_component(component_config: SungrowCounterSetup):
        return SungrowCounter(device_config, component_config, client)

    def create_inverter_component(component_config: SungrowInverterSetup):
        return SungrowInverter(device_config, component_config, client)

    def update_components(components: Iterable[Union[SungrowBat, SungrowCounter, SungrowInverter]]):
        with client:
            for component in components:
                if isinstance(component, SungrowInverter):
                    with SingleComponentUpdateContext(component.fault_state):
                        pv_power = component.update()
            for component in components:
                if isinstance(component, SungrowCounter):
                    with SingleComponentUpdateContext(component.fault_state):
                        component.update(pv_power)
            for component in components:
                if isinstance(component, SungrowBat):
                    with SingleComponentUpdateContext(component.fault_state):
                        component.update()

    try:
        client = modbus.ModbusTcpClient_(device_config.configuration.ip_address, device_config.configuration.port)
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


device_descriptor = DeviceDescriptor(configuration_factory=Sungrow)
