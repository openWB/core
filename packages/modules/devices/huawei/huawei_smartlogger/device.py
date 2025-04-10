#!/usr/bin/env python3
import logging
from typing import Iterable, Union

from modules.common.abstract_device import DeviceDescriptor
from modules.common import modbus
from modules.common.configurable_device import ComponentFactoryByType, ConfigurableDevice, MultiComponentUpdater
from modules.devices.huawei.huawei_smartlogger import counter
from modules.devices.huawei.huawei_smartlogger import inverter
from modules.devices.huawei.huawei_smartlogger import bat
from modules.devices.huawei.huawei_smartlogger.config import Huawei_Smartlogger, Huawei_SmartloggerBatSetup
from modules.devices.huawei.huawei_smartlogger.config import (Huawei_SmartloggerCounterSetup,
                                                              Huawei_SmartloggerInverterSetup)


log = logging.getLogger(__name__)


huawei_smartlogger_component_classes = Union[bat.Huawei_SmartloggerBat,
                                             counter.Huawei_SmartloggerCounter,
                                             inverter.Huawei_SmartloggerInverter]


def create_device(device_config: Huawei_Smartlogger):
    client = None

    def create_bat_component(component_config: Huawei_SmartloggerBatSetup):
        nonlocal client
        return bat.Huawei_SmartloggerBat(component_config, device_id=device_config.id, tcp_client=client)

    def create_counter_component(component_config: Huawei_SmartloggerCounterSetup):
        nonlocal client
        return counter.Huawei_SmartloggerCounter(component_config, device_id=device_config.id, tcp_client=client)

    def create_inverter_component(component_config: Huawei_SmartloggerInverterSetup):
        nonlocal client
        return inverter.Huawei_SmartloggerInverter(component_config, device_id=device_config.id, tcp_client=client)

    def update_components(components: Iterable[huawei_smartlogger_component_classes]):
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
            counter=create_counter_component,
            inverter=create_inverter_component,
        ),
        component_updater=MultiComponentUpdater(update_components)
    )


device_descriptor = DeviceDescriptor(configuration_factory=Huawei_Smartlogger)
