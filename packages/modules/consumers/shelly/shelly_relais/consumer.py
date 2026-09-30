#!/usr/bin/env python3
from modules.common import req
from typing import Optional, Dict
from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_state import ConsumerState
from modules.common.component_type import ComponentType
from modules.common.configurable_consumer import ConfigurableConsumer
from modules.common.simcount._simcounter import SimCounterConsumer
from modules.consumers.shelly.shelly_relais.config import ShellyRelais
from modules.devices.shelly.shelly.status_handler import get_generation, request_status


def create_consumer(config: ShellyRelais):
    sim_counter: Optional[SimCounterConsumer] = None
    model: Optional[str] = None
    generation: int = 1

    def initializer():
        nonlocal sim_counter, generation, model
        sim_counter = SimCounterConsumer(config.id, ComponentType.CONSUMER)
        generation, model = get_generation(config.configuration.ip_address)

    def error_handler() -> None:
        initializer()

    def switch_on() -> None:
        if generation == 1:
            url = f"http://{config.configuration.ip_address}/relay/{config.configuration.channel}?turn=on"
        else:
            chan = config.configuration.channel
            # gen 2 will das als on cmd /rpc/Switch.Set?id=100&on=true
            url = f"http://{config.configuration.ip_address}/rpc/Switch.Set?id={chan}&on=true"
        if config.configuration.username and config.configuration.password:
            auth = (config.configuration.username, config.configuration.password)
        else:
            auth = None
        req.get_http_session().get(url, auth=auth, timeout=3)

    def switch_off() -> None:
        if generation == 1:
            url = f"http://{config.configuration.ip_address}/relay/{config.configuration.channel}?turn=off"
        else:
            chan = config.configuration.channel
            # gen 2 will das als on cmd /rpc/Switch.Set?id=100&on=true
            url = f"http://{config.configuration.ip_address}/rpc/Switch.Set?id={chan}&on=false"
        if config.configuration.username and config.configuration.password:
            auth = (config.configuration.username, config.configuration.password)
        else:
            auth = None
        req.get_http_session().get(url, auth=auth, timeout=3)

    def update() -> ConsumerState:
        status = request_status(config.configuration.ip_address, generation)
        state = parse_state(status)
        return ConsumerState(
            state=state
        )

    def parse_state(status: Dict) -> bool:
        try:
            return status["switch:0"]["output"]
        except (KeyError, TypeError):
            raise Exception("Schaltstatus des Relais nicht lesbar.")

    return ConfigurableConsumer(consumer_config=config,
                                initializer=initializer,
                                error_handler=error_handler,
                                switch_on=switch_on,
                                switch_off=switch_off,
                                update=update,)


device_descriptor = DeviceDescriptor(configuration_factory=ShellyRelais)
