#!/usr/bin/env python3
from modules.common.abstract_device import DeviceDescriptor
from modules.common.configurable_consumer import ConfigurableConsumer
from modules.consumers.generic.extra_meter_only.config import ExtraMeterOnly


def create_consumer(config: ExtraMeterOnly):
    return ConfigurableConsumer(consumer_config=config)


device_descriptor = DeviceDescriptor(configuration_factory=ExtraMeterOnly)
