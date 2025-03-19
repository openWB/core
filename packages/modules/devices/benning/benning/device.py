#!/usr/bin/env python3
import logging
from modules.common.abstract_device import DeviceDescriptor
from modules.devices.benning.benning.config import Benning
from modules.devices.generic.json.device import create_device as create_device_json
log = logging.getLogger(__name__)


def create_device(device_config: Benning):
    return create_device_json(device_config)


device_descriptor = DeviceDescriptor(configuration_factory=Benning)
