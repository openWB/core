#!/usr/bin/env python3
import logging
from typing import Iterable, Union, List

from modules.common import modbus
from modules.common.abstract_device import DeviceDescriptor
from modules.common.configurable_device import ComponentFactoryByType, ConfigurableDevice, MultiComponentUpdater
from modules.devices.solaredge.solaredge.bat import SolaredgeBat
from modules.devices.solaredge.solaredge.counter import SolaredgeCounter
from modules.devices.solaredge.solaredge.external_inverter import SolaredgeExternalInverter
from modules.devices.solaredge.solaredge.inverter import SolaredgeInverter
from modules.devices.solaredge.solaredge.config import (Solaredge, SolaredgeBatSetup, SolaredgeCounterSetup,
                                                        SolaredgeExternalInverterSetup, SolaredgeInverterSetup)
from modules.devices.solaredge.solaredge.meter import SolaredgeMeterRegisters

log = logging.getLogger(__name__)

solaredge_component_classes = Union[SolaredgeBat, SolaredgeCounter,
                                    SolaredgeExternalInverter, SolaredgeInverter]
default_unit_id = 85
synergy_unit_identifier = 160
reconnect_delay = 1.2


def set_component_registers(components: Iterable[solaredge_component_classes],
                            synergy_units: int,
                            modbus_id: int) -> None:
    meters: List[Union[SolaredgeExternalInverter, SolaredgeCounter, None]] = [None]*3
    for component in components:
        if (isinstance(component, (SolaredgeExternalInverter, SolaredgeCounter)) and
                component.component_config.configuration.modbus_id == modbus_id):
            # Registerverschibung nur für Komponenten mit gleicher Modbus-ID, da diese am gleichen Haupt-WR hängen und
            # die gleichen Synergy-Units haben.
            meters[component.component_config.configuration.meter_id-1] = component

    # https://www.solaredge.com/sites/default/files/sunspec-implementation-technical-note.pdf:
    # Only enabled meters are readable, i.e. if meter 1 and 3 are enabled, they are readable as 1st meter and 2nd
    # meter (and the 3rd meter isn't readable).
    for meter_id, meter in enumerate(filter(None, meters), start=1):
        log.debug(
            "%s: internal meter id: %d, synergy units: %s", meter.component_config.name, meter_id, synergy_units
        )
        meter.registers = SolaredgeMeterRegisters(meter_id, synergy_units)


def create_device(device_config: Solaredge):
    client = None

    def create_bat_component(component_config: SolaredgeBatSetup):
        nonlocal client
        return SolaredgeBat(component_config, device_id=device_config.id, client=client)

    def create_counter_component(component_config: SolaredgeCounterSetup):
        nonlocal client, device
        synergy_units = get_synergy_units(component_config)
        counter = SolaredgeCounter(component_config, client=client)
        # neue Komponente wird erst nach Instanziierung device.components hinzugefügt
        components = list(device.components.values())
        components.append(counter)
        set_component_registers(components, synergy_units, component_config.configuration.modbus_id)
        return counter

    def create_inverter_component(component_config: SolaredgeInverterSetup):
        nonlocal client
        return SolaredgeInverter(component_config, client=client)

    def create_external_inverter_component(component_config: SolaredgeExternalInverterSetup):
        nonlocal client, device
        synergy_units = get_synergy_units(component_config)
        external_inverter = SolaredgeExternalInverter(component_config, client=client)
        components = list(device.components.values())
        components.append(external_inverter)
        set_component_registers(components, synergy_units, component_config.configuration.modbus_id)
        return external_inverter

    def update_components(components: Iterable[Union[SolaredgeBat, SolaredgeCounter, SolaredgeInverter]]):
        nonlocal client
        with client:
            for component in components:
                component.update()

    def get_synergy_units(component_config: Union[SolaredgeBatSetup,
                                                  SolaredgeCounterSetup,
                                                  SolaredgeInverterSetup,
                                                  SolaredgeExternalInverterSetup]) -> None:
        nonlocal client
        if client.read_holding_registers(40121, modbus.ModbusDataType.UINT_16,
                                         unit=component_config.configuration.modbus_id
                                         ) == synergy_unit_identifier:
            # Snyergy-Units vom Haupt-WR des angeschlossenen Meters ermitteln. Es kann mehrere Haupt-WR mit
            # unterschiedlichen Modbus-IDs im Verbund geben.
            log.debug("Synergy Units supported")
            synergy_units = int(client.read_holding_registers(
                40129, modbus.ModbusDataType.UINT_16,
                unit=component_config.configuration.modbus_id)) or 1
            log.debug(
                f"Synergy Units detected for Modbus ID {component_config.configuration.modbus_id}: {synergy_units}")
        else:
            synergy_units = 1
        return synergy_units

    def initializer():
        nonlocal client
        client = modbus.ModbusTcpClient_(device_config.configuration.ip_address,
                                         device_config.configuration.port,
                                         reconnect_delay=reconnect_delay)

    device = ConfigurableDevice(
        device_config=device_config,
        initializer=initializer,
        component_factory=ComponentFactoryByType(
            bat=create_bat_component,
            counter=create_counter_component,
            external_inverter=create_external_inverter_component,
            inverter=create_inverter_component,
        ),
        component_updater=MultiComponentUpdater(update_components)
    )
    return device


device_descriptor = DeviceDescriptor(configuration_factory=Solaredge)
