#!/usr/bin/env python3
from modules.common.component_setup import ComponentSetup
from typing import Optional
from ..vendor import vendor_descriptor

from dataclasses import dataclass, field


class GenericModbusConfiguration:
    def __init__(self, ip_address: Optional[str] = None, port: int = 502):
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
class RegisterConfig:
    reg_address: Optional[int] = None
    reg_type: Optional[str] = None
    byteorder: Optional[str] = None
    wordorder: Optional[str] = None


@dataclass
class GenericModbusCounterConfiguration:
    modbus_id: int = 105
    voltage_L1: RegisterConfig = field(default_factory=RegisterConfig)
    voltage_L2: RegisterConfig = field(default_factory=RegisterConfig)
    voltage_L3: RegisterConfig = field(default_factory=RegisterConfig)
    current_L1: RegisterConfig = field(default_factory=RegisterConfig)
    current_L2: RegisterConfig = field(default_factory=RegisterConfig)
    current_L3: RegisterConfig = field(default_factory=RegisterConfig)
    powers_L1: RegisterConfig = field(default_factory=RegisterConfig)
    powers_L2: RegisterConfig = field(default_factory=RegisterConfig)
    powers_L3: RegisterConfig = field(default_factory=RegisterConfig)
    power_factor_L1: RegisterConfig = field(default_factory=RegisterConfig)
    power_factor_L2: RegisterConfig = field(default_factory=RegisterConfig)
    power_factor_L3: RegisterConfig = field(default_factory=RegisterConfig)
    imported: RegisterConfig = field(default_factory=RegisterConfig)
    exported: RegisterConfig = field(default_factory=RegisterConfig)
    power: RegisterConfig = field(default_factory=RegisterConfig)
    frequency: RegisterConfig = field(default_factory=RegisterConfig)
    serial_number: RegisterConfig = field(default_factory=RegisterConfig)


class GenericModbusCounterSetup(ComponentSetup[GenericModbusCounterConfiguration]):
    def __init__(self,
                 name: str = "Universeller Modbus Zähler",
                 type: str = "counter",
                 id: int = 0,
                 configuration: GenericModbusCounterConfiguration = None) -> None:
        super().__init__(name, type, id, configuration or GenericModbusCounterConfiguration())


@dataclass
class GenericModbusBatConfiguration:
    modbus_id: int = 100
    current_L1: RegisterConfig = field(default_factory=RegisterConfig)
    current_L2: RegisterConfig = field(default_factory=RegisterConfig)
    current_L3: RegisterConfig = field(default_factory=RegisterConfig)
    imported: RegisterConfig = field(default_factory=RegisterConfig)
    exported: RegisterConfig = field(default_factory=RegisterConfig)
    power: RegisterConfig = field(default_factory=RegisterConfig)
    soc: RegisterConfig = field(default_factory=RegisterConfig)
    serial_number: RegisterConfig = field(default_factory=RegisterConfig)


class GenericModbusBatSetup(ComponentSetup[GenericModbusBatConfiguration]):
    def __init__(self,
                 name: str = "Universeller Modbus Batterie",
                 type: str = "bat",
                 id: int = 0,
                 configuration: GenericModbusBatConfiguration = None) -> None:
        super().__init__(name, type, id, configuration or GenericModbusBatConfiguration())


@dataclass
class GenericModbusInverterConfiguration:
    modbus_id: int = 100
    current_L1: RegisterConfig = field(default_factory=RegisterConfig)
    current_L2: RegisterConfig = field(default_factory=RegisterConfig)
    current_L3: RegisterConfig = field(default_factory=RegisterConfig)
    imported: RegisterConfig = field(default_factory=RegisterConfig)
    exported: RegisterConfig = field(default_factory=RegisterConfig)
    power: RegisterConfig = field(default_factory=RegisterConfig)
    dc_power: RegisterConfig = field(default_factory=RegisterConfig)
    serial_number: RegisterConfig = field(default_factory=RegisterConfig)


class GenericModbusInverterSetup(ComponentSetup[GenericModbusInverterConfiguration]):
    def __init__(self,
                 name: str = "Universeller Modbus Wechselrichter",
                 type: str = "inverter",
                 id: int = 0,
                 configuration: GenericModbusInverterConfiguration = None) -> None:
        super().__init__(name, type, id, configuration or GenericModbusInverterConfiguration())
