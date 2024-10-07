#!/usr/bin/env python3
import logging
from typing import Iterable, Union, List

from modules.common import modbus
from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_context import SingleComponentUpdateContext
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
    def create_bat_component(component_config: SolaredgeBatSetup):
        return SolaredgeBat(device_config.id, component_config, client)

    def create_counter_component(component_config: SolaredgeCounterSetup):
        nonlocal device
        synergy_units = get_synergy_units(component_config)
        set_component_registers(device.components.values(), synergy_units, component_config.configuration.modbus_id)
        return SolaredgeCounter(device_config.id, component_config, client)

    def create_inverter_component(component_config: SolaredgeInverterSetup):
        nonlocal device
        nonlocal inverter_counter
        inverter_counter += 1
        synergy_units = get_synergy_units(component_config)
        set_component_registers(device.components.values(), synergy_units, component_config.configuration.modbus_id)
        return SolaredgeInverter(device_config.id, component_config, client)

    def create_external_inverter_component(component_config: SolaredgeExternalInverterSetup):
        nonlocal device
        nonlocal inverter_counter
        inverter_counter += 1
        synergy_units = get_synergy_units(component_config)
        set_component_registers(device.components.values(), synergy_units, component_config.configuration.modbus_id)
        return SolaredgeExternalInverter(device_config.id, component_config, client)

    def update_components(components: Iterable[Union[SolaredgeBat, SolaredgeCounter, SolaredgeInverter]]):
        with client:
            for component in components:
                with SingleComponentUpdateContext(component.fault_state):
                    component.update()

    def get_synergy_units(component_config: Union[SolaredgeBatSetup,
                                                  SolaredgeCounterSetup,
                                                  SolaredgeInverterSetup,
                                                  SolaredgeExternalInverterSetup]) -> None:
        if (client.read_holding_registers(40121, modbus.ModbusDataType.UINT_16,
                                          unit=component_config.configuration.modbus_id
                                          ) == synergy_unit_identifier and
                (component_config.type == "external_inverter" or component_config.type == "counter")):
            # Snyergy-Units vom Haupt-WR des angeschlossenen Meters ermitteln. Es kann mehrere Haupt-WR mit
            # unterschiedlichen Modbus-IDs im Verbund geben.
            log.debug("Synergy Units supported")
            synergy_units = int(client.read_holding_registers(
                40129, modbus.ModbusDataType.UINT_16,
                unit=component_config.configuration.modbus_id)) or 1
            log.debug("Synergy Units detected: %s", synergy_units)
            return synergy_units
    try:
        inverter_counter = 0
        client = modbus.ModbusTcpClient_(device_config.configuration.ip_address,
                                         device_config.configuration.port,
                                         reconnect_delay=reconnect_delay)
        device = ConfigurableDevice(
            device_config=device_config,
            component_factory=ComponentFactoryByType(
                bat=create_bat_component,
                counter=create_counter_component,
                external_inverter=create_external_inverter_component,
                inverter=create_inverter_component,
            ),
            component_updater=MultiComponentUpdater(update_components)
        )
    except Exception:
        log.exception("Fehler in create_device")


device_descriptor = DeviceDescriptor(configuration_factory=Solaredge)
