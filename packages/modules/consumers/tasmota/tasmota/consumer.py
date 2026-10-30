#!/usr/bin/env python3
import logging
from typing import Optional

from modules.common import req
from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_state import ConsumerState
from modules.common.configurable_consumer import ConfigurableConsumer
from modules.consumers.tasmota.tasmota.config import Tasmota

log = logging.getLogger(__name__)


def create_consumer(config: Tasmota):
    session: Optional[req.CustomSession] = None

    def initializer():
        nonlocal session
        session = req.get_http_session()

    def error_handler() -> None:
        initializer()

    def update() -> ConsumerState:
        # Status 0 liefert Relais- und Energiemesswerte in einer Antwort.
        url = f"http://{config.configuration.ip_address}/cm?cmnd=Status%200"
        response = session.get(url, timeout=5).json()
        state = bool(response["Status"]["Power"])
        energy = response["StatusSNS"].get("ENERGY")
        # Ohne Energiemessung (reines Schaltrelais) bleibt power 0.
        power = float(energy["Power"]) if energy else 0.0
        return ConsumerState(power=power, state=state)

    def switch_on() -> None:
        session.get(f"http://{config.configuration.ip_address}/cm?cmnd=Power%20on", timeout=5)

    def switch_off() -> None:
        session.get(f"http://{config.configuration.ip_address}/cm?cmnd=Power%20off", timeout=5)

    return ConfigurableConsumer(consumer_config=config,
                                initializer=initializer,
                                error_handler=error_handler,
                                update=update,
                                switch_on=switch_on,
                                switch_off=switch_off)


device_descriptor = DeviceDescriptor(configuration_factory=Tasmota)
