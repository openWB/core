#!/usr/bin/env python3
import logging
from typing import Iterable, Union

from modules.common import modbus
from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_context import SingleComponentUpdateContext
from modules.common.configurable_device import ComponentFactoryByType, ConfigurableDevice, MultiComponentUpdater
from modules.devices.solarmax.solarmax.inverter import SolarmaxInverter
from modules.devices.solarmax.solarmax.bat import SolarmaxBat
from modules.devices.solarmax.solarmax.counter_maxstorage import SolarmaxMsCounter
from modules.devices.solarmax.solarmax.inverter_maxstorage import SolarmaxMsInverter
from modules.devices.solarmax.solarmax.config import (Solarmax,
                                                      SolarmaxBatSetup, SolarmaxMsCounterSetup,
                                                      SolarmaxInverterSetup, SolarmaxMsInverterSetup)

log = logging.getLogger(__name__)


def create_device(device_config: Solarmax):
    client = None

    def create_bat_component(component_config: SolarmaxBatSetup):
        return SolarmaxBat(component_config, device_id=device_config.id, client=client)

    def create_inverter_component(component_config: SolarmaxInverterSetup):
        return SolarmaxInverter(component_config, device_id=device_config.id, client=client)

    def create_inverter_ms_component(component_config: SolarmaxMsInverterSetup):
        return SolarmaxMsInverter(component_config, device_id=device_config.id, client=client)

    def create_counter_ms_component(component_config: SolarmaxMsCounterSetup):
        return SolarmaxMsCounter(component_config, device_id=device_config.id, client=client)

    def update_components(components: Iterable[Union[SolarmaxBat, SolarmaxInverter,
                                                     SolarmaxMsCounter, SolarmaxMsInverter]]):
        with client:
            for component in components:
                with SingleComponentUpdateContext(component.fault_state):
                    component.update()

    def initializer():
        nonlocal client
        client = modbus.ModbusTcpClient_(device_config.configuration.ip_address, device_config.configuration.port)

    return ConfigurableDevice(
        device_config=device_config,
        initializer=initializer,
        component_factory=ComponentFactoryByType(
            bat=create_bat_component,
            inverter=create_inverter_component,
            counter_maxstorage=create_counter_ms_component,
            inverter_maxstorage=create_inverter_ms_component,

        ),
        component_updater=MultiComponentUpdater(update_components)
    )


device_descriptor = DeviceDescriptor(
    configuration_factory=Solarmax,
    compatibility_device_note="Kann nicht aktiv laden. Steuerbar ab Solarmax Firmware 3.4.4. Zur Nutzung muss die "
    "Funktion 'Connectivity+' durch den Solarmax Support freigeschaltet werden.")
