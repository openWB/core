#!/usr/bin/env python3
from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_state import ConsumerState
from modules.common.component_type import ComponentType
from modules.common.configurable_consumer import ConfigurableConsumer
from modules.common.simcount._simcounter import SimCounterConsumer
from modules.consumers.shelly.shelly_pm.config import ShellyPM
from modules.devices.shelly.shelly.status_handler import get_generation, request_status, parse_data


def create_consumer(config: ShellyPM):
    sim_counter = None
    generation = 1

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
        return ConsumerState(
            power=power,
            imported=imported,
            exported=exported,
            voltages=voltages,
            currents=currents,
            powers=powers,
        )

    return ConfigurableConsumer(consumer_config=config,
                                initializer=initializer,
                                error_handler=error_handler,
                                update=update,)


device_descriptor = DeviceDescriptor(configuration_factory=ShellyPM)
