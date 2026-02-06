#!/usr/bin/env python3
import logging

from modules.common import req
from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_state import ConsumerState
from modules.common.configurable_consumer import ConfigurableConsumer
from modules.common.simcount._simcounter import SimCounterConsumer
from modules.consumers.generic.http.config import Http
from modules.devices.generic.http.api import create_request_function, create_request_function_array

log = logging.getLogger(__name__)


def create_consumer(config: Http):
    session = None
    sim_counter = None
    get_power = None
    get_imported = None
    get_exported = None
    get_currents = None
    get_temperatures = None

    def initializer():
        nonlocal session, sim_counter, get_power, get_imported, get_exported, get_currents, get_temperatures
        session = req.get_http_session()
        sim_counter = SimCounterConsumer(config.id, config.type)

        get_power = create_request_function(config.configuration.url, config.configuration.power_path)
        get_imported = create_request_function(config.configuration.url, config.configuration.imported_path)
        get_exported = create_request_function(config.configuration.url, config.configuration.exported_path)
        get_currents = create_request_function_array(config.configuration.url, [
            config.configuration.current_l1_path,
            config.configuration.current_l2_path,
            config.configuration.current_l3_path,
        ])
        get_temperatures = create_request_function(config.configuration.url, config.configuration.temperatures_path)

    def update() -> None:
        nonlocal session, sim_counter, get_power, get_imported, get_exported, get_currents, get_temperatures
        power = get_power(session)
        exported = get_exported(session)
        imported = get_imported(session)
        currents = get_currents(session)
        temperatures = get_temperatures(session)
        if imported is None or exported is None:
            imported, exported = sim_counter.sim_count(power)
        return ConsumerState(
            power=power,
            currents=currents,
            imported=imported,
            exported=exported,
            temperatures=temperatures if isinstance(temperatures, list) else [temperatures],
        )

    return ConfigurableConsumer(consumer_config=config,
                                module_initializer=initializer,
                                update=update)


device_descriptor = DeviceDescriptor(configuration_factory=Http)
