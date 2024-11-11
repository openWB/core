#!/usr/bin/env python3
from typing import Dict
from modules.common.component_state import IoState
from modules.common.configurable_io import ConfigurableIo
from modules.io_devices.dimm_kit.config import IoLan
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
                parsed_answer = get_version_by_telnet(VALID_VERSIONS[0], config.configuration.ip_address)
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
            # 1-4th channel test 0-5V voltage, 5-8th channel test 0-25mA current value
            analog_input={str(i): client.read_input_registers(
                i-1, ModbusDataType.UINT_8, unit=config.configuration.modbus_id)/1024 for i in range(1, 9)},
            digital_input={str(i): client.read_coils(i-1, 1, unit=config.configuration.modbus_id) for i in range(1, 9)},
            digital_output={str(i): client.read_coils(i-1, 1,
                                                      unit=config.configuration.modbus_id) for i in range(16, 24)})

    def write(digital_output: Dict[int, int]) -> None:
        for i, value in digital_output.items():
            client.write_single_coil(i-1, value, unit=config.configuration.modbus_id)

    version = False
    client = ModbusTcpClient_(config.configuration.ip_address, config.configuration.port)
    for i, value in config.output["digital"].items():
        client.write_single_coil(i-1, value, unit=config.configuration.modbus_id)
    return ConfigurableIo(config=config, component_reader=read, component_writer=write)


device_descriptor = DeviceDescriptor(configuration_factory=IoLan)
