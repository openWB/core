#!/usr/bin/env python3
import logging
from typing import Iterable, Union

from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_context import SingleComponentUpdateContext
from modules.common.configurable_device import ConfigurableDevice, ComponentFactoryByType, MultiComponentUpdater
from modules.common.modbus import ModbusTcpClient_
from modules.devices.varta.varta.inverter import VartaInverter
from modules.devices.varta.varta.bat_api import VartaBatApi
from modules.devices.varta.varta.bat_modbus import VartaBatModbus
from modules.devices.varta.varta.config import (Varta, VartaBatApiSetup, VartaBatModbusSetup,
                                                VartaCounterSetup, VartaInverterSetup)
from modules.devices.varta.varta.counter import VartaCounter

log = logging.getLogger(__name__)


def create_device(device_config: Varta):
    client = None

    def create_bat_api_component(component_config: VartaBatApiSetup):
        return VartaBatApi(component_config,
                           device_id=device_config.id,
                           ip_address=device_config.configuration.ip_address)

    def create_bat_modbus_component(component_config: VartaBatModbusSetup):
        return VartaBatModbus(component_config,
                              device_id=device_config.id,
                              modbus_id=device_config.configuration.modbus_id,
                              client=client)

    def create_counter_component(component_config: VartaCounterSetup):
        return VartaCounter(component_config,
                            device_id=device_config.id,
                            modbus_id=device_config.configuration.modbus_id,
                            client=client)

    def create_inverter_component(component_config: VartaInverterSetup):
        return VartaInverter(component_config,
                             device_id=device_config.id,
                             modbus_id=device_config.configuration.modbus_id,
                             client=client)

    def update_components(components: Iterable[Union[VartaBatApi, VartaBatModbus, VartaCounter, VartaInverter]]):
        with client:
            for component in components:
                if isinstance(component, (VartaBatModbus, VartaCounter, VartaInverter)):
                    with SingleComponentUpdateContext(component.fault_state):
                        component.update()
        for component in components:
            if isinstance(component, (VartaBatApi)):
                with SingleComponentUpdateContext(component.fault_state):
                    component.update()

    def initializer():
        nonlocal client
        client = ModbusTcpClient_(device_config.configuration.ip_address, device_config.configuration.port)

    return ConfigurableDevice(
        device_config=device_config,
        initializer=initializer,
        component_factory=ComponentFactoryByType(
            bat_api=create_bat_api_component,
            bat_modbus=create_bat_modbus_component,
            counter=create_counter_component,
            inverter=create_inverter_component
        ),
        component_updater=MultiComponentUpdater(update_components)
    )


device_descriptor = DeviceDescriptor(
    configuration_factory=Varta,
    compatibility_bat_note="Es kann nur eine maximale Entladeleistung vorgegeben werden. "
    "Eine aktive Ladung ist nicht möglich.")
