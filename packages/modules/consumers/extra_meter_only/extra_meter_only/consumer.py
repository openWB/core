#!/usr/bin/env python3
import logging

from modules.common.abstract_device import DeviceDescriptor
from modules.common.configurable_consumer import ConfigurableConsumer
from modules.consumers.extra_meter_only.extra_meter_only.config import ExtraMeterOnly

log = logging.getLogger(__name__)


def create_consumer(config: ExtraMeterOnly):
    return ConfigurableConsumer(consumer_config=config)


device_descriptor = DeviceDescriptor(configuration_factory=ExtraMeterOnly)
