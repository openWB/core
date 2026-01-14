#!/usr/bin/env python3
import logging
from modules.common.abstract_consumer import AbstractConsumer
from modules.common.abstract_device import DeviceDescriptor
from modules.common.configurable_consumer import ConfigurableConsumer
from modules.consumers.generic.counter.config import CounterConfiguration, Counter

log = logging.getLogger(__name__)


class CounterConsumer(AbstractConsumer):
    def __init__(self, config: Counter) -> None:
        self.config = config


def create_consumer(config: CounterConfiguration):
    return ConfigurableConsumer(CounterConsumer(config))


device_descriptor = DeviceDescriptor(configuration_factory=Counter)
