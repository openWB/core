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
from modules.devices.huawei.huawei.type import HuaweiType

log = logging.getLogger(__name__)


def create_device(device_config: Huawei):
    def create_bat_component(component_config: HuaweiBatSetup):
        return HuaweiBat(device_config.id,
                         component_config,
                         device_config.configuration.modbus_id,
                         HuaweiType(device_config.configuration.type))

    def create_counter_component(component_config: HuaweiCounterSetup):
        return HuaweiCounter(device_config.id,
                             component_config,
                             device_config.configuration.modbus_id,
                             HuaweiType(device_config.configuration.type))

    def create_inverter_component(component_config: HuaweiInverterSetup):
        return HuaweiInverter(device_config.id,
                              component_config,
                              device_config.configuration.modbus_id,
                              HuaweiType(device_config.configuration.type))

    def update_components(components: Iterable[Union[HuaweiBat, HuaweiCounter, HuaweiInverter]]):
        with client:
            for component in components:
                with SingleComponentUpdateContext(component.fault_state):
                    component.update(client)

    try:
        if HuaweiType(device_config.configuration.type) == HuaweiType.SDongle:
            client = ModbusTcpClient_(device_config.configuration.ip_address,
                                      device_config.configuration.port, sleep_after_connect=7)
        else:
            client = ModbusTcpClient_(device_config.configuration.ip_address,
                                      device_config.configuration.port)
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


device_descriptor = DeviceDescriptor(configuration_factory=Huawei)
