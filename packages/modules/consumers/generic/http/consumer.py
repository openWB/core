#!/usr/bin/env python3
import logging

from modules.common import req
from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_state import ConsumerState
from modules.common.configurable_consumer import ConfigurableConsumer
from modules.common.simcount._simcounter import SimCounterConsumer
from modules.consumers.generic.http.config import Http
from modules.devices.generic.http.api import (create_post_function, create_request_function,
                                              create_request_function_array)
log = logging.getLogger(__name__)


def create_consumer(config: Http):
    session = None
    sim_counter = None
    get_power = None
    get_imported = None
    get_exported = None
    get_currents = None
    get_temperatures = None
    post_set_power_limit = None
    post_switch_on = None
    post_switch_off = None

    def initializer():
        nonlocal session, sim_counter
        nonlocal get_power, get_imported, get_exported, get_currents, get_temperatures
        nonlocal post_set_power_limit, post_switch_on, post_switch_off
        if not config.configuration.url.startswith('https://'):
            raise ValueError("Only HTTPS URLs allowed for security")
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
        post_set_power_limit = create_post_function(config.configuration.url, config.configuration.set_power_limit_path)
        post_switch_on = create_post_function(config.configuration.url, config.configuration.switch_on_path)
        post_switch_off = create_post_function(config.configuration.url, config.configuration.switch_off_path)

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

    def switch_on():
        nonlocal session, post_switch_on
        # Authorization?
        post_switch_on(session, params={"state": True})

    def switch_off():
        nonlocal session, post_switch_off
        # Authorization?
        post_switch_off(session, params={"state": False})

    def set_power_limit(power_limit: int):
        nonlocal session, post_set_power_limit
        # Authorization?
        post_set_power_limit(session, params={"power_limit": power_limit})

    return ConfigurableConsumer(consumer_config=config,
                                module_initializer=initializer,
                                update=update,
                                set_power_limit=set_power_limit,
                                switch_on=switch_on,
                                switch_off=switch_off)


device_descriptor = DeviceDescriptor(configuration_factory=Http)
