#!/usr/bin/env python3
import logging
from typing import Iterable, Union

from modules.common import modbus
from modules.common.abstract_device import DeviceDescriptor
from modules.common.configurable_device import ComponentFactoryByType, ConfigurableDevice, MultiComponentUpdater
from modules.devices.sungrow.sungrow.bat import SungrowBat
from modules.devices.sungrow.sungrow.config import Sungrow, SungrowBatSetup, SungrowCounterSetup, SungrowInverterSetup
from modules.devices.sungrow.sungrow.counter import SungrowCounter
from modules.devices.sungrow.sungrow.inverter import SungrowInverter

log = logging.getLogger(__name__)


def create_device(device_config: Sungrow):
    client = None

    def create_bat_component(component_config: SungrowBatSetup):
        nonlocal client
        return SungrowBat(component_config, device_config=device_config, client=client)

    def create_counter_component(component_config: SungrowCounterSetup):
        nonlocal client
        return SungrowCounter(component_config, device_config=device_config, client=client)

    def create_inverter_component(component_config: SungrowInverterSetup):
        nonlocal client
        return SungrowInverter(component_config, device_config=device_config, client=client)

    def update_components(components: Iterable[Union[SungrowBat, SungrowCounter, SungrowInverter]]):
        pv_power = 0
        nonlocal client
        with client:
            for component in components:
                if isinstance(component, SungrowInverter):
                    pv_power = component.update()
            for component in components:
                if isinstance(component, SungrowCounter):
                    component.update(pv_power)
            for component in components:
                if isinstance(component, SungrowBat):
                    component.update()

    def initializer():
        nonlocal client
        client = modbus.ModbusTcpClient_(device_config.configuration.ip_address, device_config.configuration.port)

    return ConfigurableDevice(
        device_config=device_config,
        initializer=initializer,
        component_factory=ComponentFactoryByType(
            bat=create_bat_component,
            counter=create_counter_component,
            inverter=create_inverter_component,
        ),
        component_updater=MultiComponentUpdater(update_components)
    )


device_descriptor = DeviceDescriptor(configuration_factory=Sungrow)
