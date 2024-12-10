#!/usr/bin/env python3
from typing import Dict
from modules.common.component_state import IoState
from modules.common.configurable_io import ConfigurableIo
from modules.io_devices.dimm_kit.config import IoLan, AnalogInputMapping, DigitalInputMapping, DigitalOutputMapping
from modules.common.version_by_telnet import get_version_by_telnet
from modules.common.modbus import ModbusDataType, ModbusTcpClient_
import logging
import socket

from modules.common.abstract_device import DeviceDescriptor

log = logging.getLogger(__name__)


VALID_VERSIONS = ["openWB DimmModul"]


def create_io(config: IoLan):
    def read():
        nonlocal version
        if version is False:
            try:
                parsed_answer = get_version_by_telnet(VALID_VERSIONS[0], config.configuration.host)
                for version in VALID_VERSIONS:
                    if version in parsed_answer:
                        version = True
                        log.debug("Firmware des openWB Dimm-& Control-Kit ist mit openWB software2 kompatibel.")
                    else:
                        version = False
                        raise ValueError
            except (ConnectionRefusedError, ValueError):
                log.exception("Dimm-Kit")
                raise Exception("Firmware des openWB Dimm-& Control-Kit ist nicht mit openWB software2 kompatibel. "
                                "Bitte den Support kontaktieren.")
            except socket.timeout:
                log.exception("Dimm-Kit")
                raise Exception("Die IP-Adresse ist nicht erreichbar. Bitte überprüfe die Einstellungen.")
        return IoState(
            # analog inputs are configured as 0-5V (AI1-AI4) and 0-25mA (AI5-AI8) as default
            # the values are reported as integers in range of 0-1024
            analog_input={
                pin.name: client.read_input_registers(
                    pin.value, ModbusDataType.UINT_16, unit=config.configuration.modbus_id
                ) for pin in AnalogInputMapping},
            digital_input={
                pin.name: client.read_coils(
                    pin.value, 1, unit=config.configuration.modbus_id
                ) for pin in DigitalInputMapping},
            digital_output={
                pin.name: client.read_coils(
                    pin.value, 1, unit=config.configuration.modbus_id
                ) for pin in DigitalOutputMapping})

    def write(digital_output: Dict[int, int]) -> None:
        for i, value in digital_output.items():
            client.write_single_coil(i-1, value, unit=config.configuration.modbus_id)

    version = False
    client = ModbusTcpClient_(config.configuration.host, config.configuration.port)
    for output, value in config.output["digital"].items():
        client.write_single_coil(DigitalOutputMapping[output].value, value, unit=config.configuration.modbus_id)
    return ConfigurableIo(config=config, component_reader=read, component_writer=write)


device_descriptor = DeviceDescriptor(configuration_factory=IoLan)
