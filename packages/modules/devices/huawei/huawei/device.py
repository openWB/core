#!/usr/bin/env python3
import logging
from pathlib import Path
from typing import Iterable, Union

from helpermodules.utils.run_command import run_command
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
    client = None

    def create_bat_component(component_config: HuaweiBatSetup):
        nonlocal client
        return HuaweiBat(component_config,
                         device_id=device_config.id,
                         modbus_id=device_config.configuration.modbus_id,
                         type=HuaweiType(device_config.configuration.type),
                         client=client)

    def create_counter_component(component_config: HuaweiCounterSetup):
        nonlocal client
        return HuaweiCounter(component_config,
                             device_id=device_config.id,
                             modbus_id=device_config.configuration.modbus_id,
                             type=HuaweiType(device_config.configuration.type),
                             client=client)

    def create_inverter_component(component_config: HuaweiInverterSetup):
        nonlocal client
        return HuaweiInverter(component_config,
                              device_id=device_config.id,
                              modbus_id=device_config.configuration.modbus_id,
                              type=HuaweiType(device_config.configuration.type),
                              client=client)

    def update_components(components: Iterable[Union[HuaweiBat, HuaweiCounter, HuaweiInverter]]):
        nonlocal client
        with client:
            for component in components:
                with SingleComponentUpdateContext(component.fault_state, update_always=False):
                    component.update()

    def initializer():
        nonlocal client
        if HuaweiType(device_config.configuration.type) == HuaweiType.SDongle:
            client = ModbusTcpClient_(device_config.configuration.ip_address,
                                      device_config.configuration.port, sleep_after_connect=7)
        if HuaweiType(device_config.configuration.type) == HuaweiType.HuaweiKit:
            client = ModbusTcpClient_("192.168.193.126", 8899)
        else:
            client = ModbusTcpClient_(device_config.configuration.ip_address,
                                      device_config.configuration.port)

    def error_handler():
        run_command(f"{Path(__file__).resolve().parents[4]}/modules/common/restart_protoss_admin")

    return ConfigurableDevice(
        device_config=device_config,
        initializer=initializer,
        error_handler=error_handler,
        component_factory=ComponentFactoryByType(
            bat=create_bat_component,
            counter=create_counter_component,
            inverter=create_inverter_component,
        ),
        component_updater=MultiComponentUpdater(update_components)
    )


device_descriptor = DeviceDescriptor(configuration_factory=Huawei)
