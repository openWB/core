#!/usr/bin/env python3
import logging
from pathlib import Path
from typing import Iterable, Union

from helpermodules.utils.run_command import run_command
from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_context import SingleComponentUpdateContext
from modules.common.configurable_device import ComponentFactoryByType, ConfigurableDevice, MultiComponentUpdater
from modules.common.modbus import ModbusTcpClient_
from modules.devices.huawei.huawei_emma.bat import Huawei_EmmaBat
from modules.devices.huawei.huawei_emma.config import Huawei_Emma, Huawei_EmmaBatSetup
from modules.devices.huawei.huawei_emma.config import Huawei_EmmaCounterSetup, Huawei_EmmaInverterSetup
from modules.devices.huawei.huawei_emma.counter import Huawei_EmmaCounter
from modules.devices.huawei.huawei_emma.inverter import Huawei_EmmaInverter

log = logging.getLogger(__name__)


def create_device(device_config: Huawei_Emma):
    client = None

    def create_bat_component(component_config: Huawei_EmmaBatSetup):
        nonlocal client
        return Huawei_EmmaBat(component_config,
                              device_id=device_config.id,
                              modbus_id=device_config.configuration.modbus_id,
                              client=client)

    def create_counter_component(component_config: Huawei_EmmaCounterSetup):
        nonlocal client
        return Huawei_EmmaCounter(component_config,
                                  device_id=device_config.id,
                                  modbus_id=device_config.configuration.modbus_id,
                                  client=client)

    def create_inverter_component(component_config: Huawei_EmmaInverterSetup):
        nonlocal client
        return Huawei_EmmaInverter(component_config,
                                   device_id=device_config.id,
                                   modbus_id=device_config.configuration.modbus_id,
                                   client=client)

    def update_components(components: Iterable[Union[Huawei_EmmaBat, Huawei_EmmaCounter, Huawei_EmmaInverter]]):
        nonlocal client
        with client:
            for component in components:
                with SingleComponentUpdateContext(component.fault_state):
                    component.update()

    def initializer():
        nonlocal client
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


device_descriptor = DeviceDescriptor(configuration_factory=Huawei_Emma)
