#!/usr/bin/env python3
import logging
from modules.common.abstract_device import DeviceDescriptor
from modules.devices.zendure.zendure.config import Zendure
from modules.devices.generic.json.device import create_device as create_device_json
log = logging.getLogger(__name__)


def create_device(device_config: Zendure):
    return create_device_json(device_config)


device_descriptor = DeviceDescriptor(configuration_factory=Zendure)
