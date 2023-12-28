#!/usr/bin/env python3
import logging

from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_state import RcrState
from modules.common.configurable_ripple_control_receiver import ConfigurableRcr
from modules.common.modbus import ModbusTcpClient_
from modules.ripple_control_receivers.io_lan_hf.config import IoLanRcr

log = logging.getLogger(__name__)


def create_ripple_control_receiver(config: IoLanRcr):
    def updater():
        r1 = client.read_coils(0x0000, 1, unit=config.configuration.modbus_id) is False
        r2 = client.read_coils(0x0001, 1, unit=config.configuration.modbus_id) is False
        return RcrState(r1, r2)
    try:
        client = ModbusTcpClient_(config.configuration.ip_address, config.configuration.port)
    except Exception:
        log.exception("Fehler in create_device")
    return ConfigurableRcr(config=config, component_updater=updater)


device_descriptor = DeviceDescriptor(configuration_factory=IoLanRcr)
