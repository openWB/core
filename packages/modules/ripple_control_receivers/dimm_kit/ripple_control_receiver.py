#!/usr/bin/env python3
from enum import Enum
import logging
import socket

from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_state import RcrState
from modules.common.modbus import ModbusTcpClient_
from modules.common.version_by_telnet import get_version_by_telnet
from modules.ripple_control_receivers.dimm_kit.config import IoLanRcr

log = logging.getLogger(__name__)


class State(Enum):
    OPENED = False
    CLOSED = True


VALID_VERSIONS = ["openWB DimmModul"]


def create_ripple_control_receiver(config: IoLanRcr):
    def updater():
        r1 = State(client.read_coils(0x0000, 1, unit=config.configuration.modbus_id))
        r2 = State(client.read_coils(0x0001, 1, unit=config.configuration.modbus_id))
        log.debug(f"RSE-Kontakt 1: {r1}, RSE-Kontakt 2: {r2}")
        if r1 == State.OPENED or r2 == State.OPENED:
            override_value = 0
        else:
            override_value = 100
        return RcrState(override_value=override_value)
    version = False
    client = ModbusTcpClient_(config.configuration.ip_address, config.configuration.port)
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
        raise Exception("Die IP-Adresse ist nicht erreichbar. Bitte den Support kontaktieren.")
    return updater


device_descriptor = DeviceDescriptor(configuration_factory=IoLanRcr)
