#!/usr/bin/env python3
import logging
from typing import Optional
from urllib.parse import quote

from modules.common import req
from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_state import ConsumerState
from modules.common.configurable_consumer import ConfigurableConsumer
from modules.consumers.esphome.esphome.config import EspHome

log = logging.getLogger(__name__)


def create_consumer(config: EspHome):
    session: Optional[req.CustomSession] = None

    def initializer():
        nonlocal session
        session = req.get_http_session()

    def error_handler() -> None:
        initializer()

    def update() -> ConsumerState:
        ip_address = config.configuration.ip_address
        sensor_name = quote(config.configuration.power_sensor_name)
        power = float(session.get(f"http://{ip_address}/sensor/{sensor_name}", timeout=5).json()["value"])

        kwargs = {}
        if config.configuration.switch_name:
            switch_name = quote(config.configuration.switch_name)
            kwargs["state"] = bool(session.get(f"http://{ip_address}/switch/{switch_name}", timeout=5).json()["value"])
        return ConsumerState(power=power, **kwargs)

    def switch_on() -> None:
        switch_name = quote(config.configuration.switch_name)
        session.post(f"http://{config.configuration.ip_address}/switch/{switch_name}/turn_on", timeout=5)

    def switch_off() -> None:
        switch_name = quote(config.configuration.switch_name)
        session.post(f"http://{config.configuration.ip_address}/switch/{switch_name}/turn_off", timeout=5)

    return ConfigurableConsumer(consumer_config=config,
                                initializer=initializer,
                                error_handler=error_handler,
                                update=update,
                                switch_on=switch_on,
                                switch_off=switch_off)


device_descriptor = DeviceDescriptor(configuration_factory=EspHome)
