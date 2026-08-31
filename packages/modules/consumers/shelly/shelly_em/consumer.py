#!/usr/bin/env python3
from modules.common.abstract_device import DeviceDescriptor
from typing import Optional
from modules.common.component_state import ConsumerState
from modules.common.component_type import ComponentType
from modules.common.configurable_consumer import ConfigurableConsumer
from modules.common.simcount._simcounter import SimCounterConsumer
from modules.consumers.shelly.shelly_em.config import ShellyEM
from modules.devices.shelly.shelly.status_handler import get_generation, request_status, parse_data


def create_consumer(config: ShellyEM):
    sim_counter: Optional[SimCounterConsumer] = None
    generation: int = 1

    def initializer():
        nonlocal sim_counter, generation
        sim_counter = SimCounterConsumer(config.id, ComponentType.CONSUMER)
        generation, _ = get_generation(config.configuration.ip_address)

    def error_handler() -> None:
        initializer()

    def update() -> ConsumerState:
        status = request_status(config.configuration.ip_address, generation)
        powers, voltages, currents, _, power, _ = parse_data(
            config.configuration.phase, config.configuration.factor, status)
        imported, exported = sim_counter.sim_count(power)
        consumer_state = ConsumerState(
            power=power,
            imported=imported,
            exported=exported,
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
