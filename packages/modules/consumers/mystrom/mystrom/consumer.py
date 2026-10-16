#!/usr/bin/env python3
import logging
from modules.common import req
from typing import Optional
from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_state import ConsumerState
from modules.common.configurable_consumer import ConfigurableConsumer
from modules.consumers.mystrom.mystrom.config import MyStrom

log = logging.getLogger(__name__)


def create_consumer(config: MyStrom):
    session: Optional[req.CustomSession] = None

    def initializer():
        nonlocal session
        session = req.get_http_session()

    def error_handler() -> None:
        initializer()

    def update() -> ConsumerState:
        resp = session.get(f"http://{config.configuration.ip_address}/report", timeout=3).json()
        power = resp["power"]
        relais = resp["relay"]
        temp = float(resp["temperature"])
        return ConsumerState(
            power=power,
            temperatures=[temp],
            state=relais
        )

    def switch_on() -> None:
        session.get(f"http://{config.configuration.ip_address}/relay?state=1", timeout=3)

    def switch_off() -> None:
        session.get(f"http://{config.configuration.ip_address}/relay?state=0", timeout=3)

    return ConfigurableConsumer(consumer_config=config,
                                initializer=initializer,
                                error_handler=error_handler,
                                update=update,
                                switch_on=switch_on,
                                switch_off=switch_off,
                                )


device_descriptor = DeviceDescriptor(configuration_factory=MyStrom)
