#!/usr/bin/env python3
from modules.common.abstract_device import DeviceDescriptor
from modules.common.configurable_consumer import ConfigurableConsumer
from modules.consumers.generic.counter.config import Counter


def create_consumer(config: Counter):
    return ConfigurableConsumer(consumer_config=config)


device_descriptor = DeviceDescriptor(configuration_factory=Counter)
