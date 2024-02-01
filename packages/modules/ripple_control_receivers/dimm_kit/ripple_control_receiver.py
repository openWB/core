#!/usr/bin/env python3
from enum import Enum
import logging

from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_state import RcrState
from modules.common.configurable_ripple_control_receiver import ConfigurableRcr
from modules.common.modbus import ModbusTcpClient_
from modules.ripple_control_receivers.dimm_kit.config import IoLanRcr

log = logging.getLogger(__name__)


class State(Enum):
    OPENED = False
    CLOSED = True


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
    try:
        client = ModbusTcpClient_(config.configuration.ip_address, config.configuration.port)
    except Exception:
        log.exception("Fehler in create_device")
    return ConfigurableRcr(config=config, component_updater=updater)


device_descriptor = DeviceDescriptor(configuration_factory=IoLanRcr)
