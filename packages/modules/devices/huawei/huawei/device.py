#!/usr/bin/env python3
import logging
from typing import Iterable, Union

from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_context import SingleComponentUpdateContext
from modules.common.configurable_device import ComponentFactoryByType, ConfigurableDevice, MultiComponentUpdater
from modules.common.modbus import ModbusTcpClient_
from modules.devices.huawei.huawei.bat import HuaweiBat
from modules.devices.huawei.huawei.config import Huawei, HuaweiBatSetup, HuaweiCounterSetup, HuaweiInverterSetup
from modules.devices.huawei.huawei.counter import HuaweiCounter
from modules.devices.huawei.huawei.inverter import HuaweiInverter

log = logging.getLogger(__name__)


def create_device(device_config: Huawei):
    client = None

    def create_bat_component(component_config: HuaweiBatSetup):
        nonlocal client
        return HuaweiBat(device_config.id, component_config, device_config.configuration.modbus_id, client)

    def create_counter_component(component_config: HuaweiCounterSetup):
        nonlocal client
        return HuaweiCounter(device_config.id, component_config, device_config.configuration.modbus_id, client)

    def create_inverter_component(component_config: HuaweiInverterSetup):
        nonlocal client
        return HuaweiInverter(device_config.id, component_config, device_config.configuration.modbus_id, client)

    def update_components(components: Iterable[Union[HuaweiBat, HuaweiCounter, HuaweiInverter]]):
        nonlocal client
        with client:
            for component in components:
                with SingleComponentUpdateContext(component.fault_state):
                    component.update()

    def initialiser():
        nonlocal client
        client = ModbusTcpClient_(device_config.configuration.ip_address,
                                  device_config.configuration.port, sleep_after_connect=7)

    return ConfigurableDevice(
        device_config=device_config,
        initialiser=initialiser,
        component_factory=ComponentFactoryByType(
            bat=create_bat_component,
            counter=create_counter_component,
            inverter=create_inverter_component,
        ),
        component_updater=MultiComponentUpdater(update_components)
    )


device_descriptor = DeviceDescriptor(configuration_factory=Huawei)
