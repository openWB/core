#!/usr/bin/env python3
from modules.common.component_setup import ComponentSetup
from ..vendor import vendor_descriptor

from typing import Optional
from dataclasses import dataclass
from modules.common.modbus import ModbusDataType, Endian


class GenericModbusConfiguration:
    def __init__(self, ip_address: str = "192.168.1.230", port: int = 502):
        self.ip_address = ip_address
        self.port = port


class GenericModbus:
    def __init__(self,
                 name: str = "Modbus",
                 type: str = "modbus",
                 id: int = 0,
                 configuration: GenericModbusConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.vendor = vendor_descriptor.configuration_factory().type
        self.id = id
        self.configuration = configuration or GenericModbusConfiguration()


@dataclass
class gerneric_modbus:
    reg_address: int
    reg_type: str
    byteorder: str
    wordorder: str


class GenericModbusCounterConfiguration:
    def __init__(self, modbus_id: int = 105,
                 voltage_L1: gerneric_modbus = gerneric_modbus(
                     reg_address=None, reg_type=None, byteorder=None, wordorder=None),
                 voltage_L2: gerneric_modbus = gerneric_modbus(
                     reg_address=None, reg_type=None, byteorder=None, wordorder=None),
                 voltage_L3: gerneric_modbus = gerneric_modbus(
                     reg_address=None, reg_type=None, byteorder=None, wordorder=None),
                 current_L1: gerneric_modbus = gerneric_modbus(
                     reg_address=None, reg_type=None, byteorder=None, wordorder=None),
                 current_L2: gerneric_modbus = gerneric_modbus(
                     reg_address=None, reg_type=None, byteorder=None, wordorder=None),
                 current_L3: gerneric_modbus = gerneric_modbus(
                     reg_address=None, reg_type=None, byteorder=None, wordorder=None),
                 powers_L1: gerneric_modbus = gerneric_modbus(
                     reg_address=None, reg_type=None, byteorder=None, wordorder=None),
                 powers_L2: gerneric_modbus = gerneric_modbus(
                     reg_address=None, reg_type=None, byteorder=None, wordorder=None),
                 powers_L3: gerneric_modbus = gerneric_modbus(
                     reg_address=None, reg_type=None, byteorder=None, wordorder=None),
                 power_factor_L1: gerneric_modbus = gerneric_modbus(
                     reg_address=None, reg_type=None, byteorder=None, wordorder=None),
                 power_factor_L2: gerneric_modbus = gerneric_modbus(
                     reg_address=None, reg_type=None, byteorder=None, wordorder=None),
                 power_factor_L3: gerneric_modbus = gerneric_modbus(
                     reg_address=None, reg_type=None, byteorder=None, wordorder=None),
                 imported: gerneric_modbus = gerneric_modbus(
                     reg_address=None, reg_type=None, byteorder=None, wordorder=None),
                 exported: gerneric_modbus = gerneric_modbus(
                     reg_address=None, reg_type=None, byteorder=None, wordorder=None),
                 power: gerneric_modbus = gerneric_modbus(
                     reg_address=None, reg_type=None, byteorder=None, wordorder=None),
                 frequency: gerneric_modbus = gerneric_modbus(
                     reg_address=None, reg_type=None, byteorder=None, wordorder=None),
                 serial_number: gerneric_modbus = gerneric_modbus(
                     reg_address=None, reg_type=None, byteorder=None, wordorder=None)):

        self.modbus_id = modbus_id
        self.voltage_L1 = voltage_L1
        self.voltage_L2 = voltage_L2
        self.voltage_L3 = voltage_L3

        self.current_L1 = current_L1
        self.current_L2 = current_L2
        self.current_L3 = current_L3

        self.powers_L1 = powers_L1
        self.powers_L2 = powers_L2
        self.powers_L3 = powers_L3

        self.power_factor_L1 = power_factor_L1
        self.power_factor_L2 = power_factor_L2
        self.power_factor_L3 = power_factor_L3

        self.imported = imported
        self.exported = exported

        self.power = power

        self.frequency = frequency

        self.serial_number = serial_number


class GenericModbusCounterSetup(ComponentSetup[GenericModbusCounterConfiguration]):
    def __init__(self,
                 name: str = "Universeller Modbus Zähler",
                 type: str = "counter",
                 id: int = 0,
                 configuration: GenericModbusCounterConfiguration = None) -> None:
        super().__init__(name, type, id, configuration or GenericModbusCounterConfiguration())


class GenericModbusBatConfiguration:
    def __init__(self, modbus_id: int = 100,
                 current_L1: gerneric_modbus = gerneric_modbus(
                     reg_address=None, reg_type=None, byteorder=None, wordorder=None),
                 current_L2: gerneric_modbus = gerneric_modbus(
                     reg_address=None, reg_type=None, byteorder=None, wordorder=None),
                 current_L3: gerneric_modbus = gerneric_modbus(
                     reg_address=None, reg_type=None, byteorder=None, wordorder=None),
                 imported: gerneric_modbus = gerneric_modbus(
                     reg_address=None, reg_type=None, byteorder=None, wordorder=None),
                 exported: gerneric_modbus = gerneric_modbus(
                     reg_address=None, reg_type=None, byteorder=None, wordorder=None),
                 power: gerneric_modbus = gerneric_modbus(
                     reg_address=None, reg_type=None, byteorder=None, wordorder=None),
                 soc: gerneric_modbus = gerneric_modbus(
                     reg_address=None, reg_type=None, byteorder=None, wordorder=None),
                 serial_number: gerneric_modbus = gerneric_modbus(
                     reg_address=None, reg_type=None, byteorder=None, wordorder=None)):

        self.modbus_id = modbus_id

        self.current_L1 = current_L1
        self.current_L2 = current_L2
        self.current_L3 = current_L3

        self.imported = imported
        self.exported = exported

        self.power = power
        self.soc = soc

        self.serial_number = serial_number


class GenericModbusBatSetup(ComponentSetup[GenericModbusBatConfiguration]):
    def __init__(self,
                 name: str = "Universeller Modbus Batterie",
                 type: str = "bat",
                 id: int = 0,
                 configuration: GenericModbusBatConfiguration = None) -> None:
        super().__init__(name, type, id, configuration or GenericModbusBatConfiguration())


class GenericModbusInverterConfiguration:
    def __init__(self, modbus_id: int = 100,
                 current_L1: gerneric_modbus = gerneric_modbus(
                     reg_address=None, reg_type=None, byteorder=None, wordorder=None),
                 current_L2: gerneric_modbus = gerneric_modbus(
                     reg_address=None, reg_type=None, byteorder=None, wordorder=None),
                 current_L3: gerneric_modbus = gerneric_modbus(
                     reg_address=None, reg_type=None, byteorder=None, wordorder=None),
                 imported: gerneric_modbus = gerneric_modbus(
                     reg_address=None, reg_type=None, byteorder=None, wordorder=None),
                 exported: gerneric_modbus = gerneric_modbus(
                     reg_address=None, reg_type=None, byteorder=None, wordorder=None),
                 power: gerneric_modbus = gerneric_modbus(
                     reg_address=None, reg_type=None, byteorder=None, wordorder=None),
                 dc_power: gerneric_modbus = gerneric_modbus(
                     reg_address=None, reg_type=None, byteorder=None, wordorder=None),
                 serial_number: gerneric_modbus = gerneric_modbus(
                     reg_address=None, reg_type=None, byteorder=None, wordorder=None)):

        self.modbus_id = modbus_id

        self.current_L1 = current_L1
        self.current_L2 = current_L2
        self.current_L3 = current_L3

        self.imported = imported
        self.exported = exported

        self.power = power
        self.dc_power = dc_power

        self.serial_number = serial_number


class GenericModbusInverterSetup(ComponentSetup[GenericModbusInverterConfiguration]):
    def __init__(self,
                 name: str = "Universeller Modbus Wechselrichter",
                 type: str = "inverter",
                 id: int = 0,
                 configuration: GenericModbusInverterConfiguration = None) -> None:
        super().__init__(name, type, id, configuration or GenericModbusInverterConfiguration())
