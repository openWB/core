#!/usr/bin/env python3
from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_state import ConsumerState
from modules.common.configurable_consumer import ConfigurableConsumer
from modules.consumers.shelly.shelly_em.config import ShellyEM
from modules.devices.shelly.shelly.status_handler import get_generation, request_status, parse_data


def create_consumer(config: ShellyEM):
    generation: int = 1

    def initializer():
        nonlocal generation
        generation, _ = get_generation(config.configuration.ip_address)

    def error_handler() -> None:
        initializer()

    def update() -> ConsumerState:
        status = request_status(config.configuration.ip_address, generation)
        powers, voltages, currents, _, power, _ = parse_data(1, config.configuration.factor, status)
        consumer_state = ConsumerState(
            power=power,
            powers=powers,
        )
        if voltages is not None:
            consumer_state.voltages = voltages
        if currents is not None:
            consumer_state.currents = currents
        return consumer_state

    return ConfigurableConsumer(consumer_config=config,
                                initializer=initializer,
                                error_handler=error_handler,
                                update=update,)


device_descriptor = DeviceDescriptor(configuration_factory=ShellyEM)
