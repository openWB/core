#!/usr/bin/env python3
import logging
from typing import Optional, Callable

from modules.common import req
from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_state import ConsumerState
from modules.common.component_type import ComponentType
from modules.common.configurable_consumer import ConfigurableConsumer, SetLimitData
from modules.common.simcount._simcounter import SimCounterConsumer
from modules.consumers.generic.http.config import Http
from modules.devices.generic.http.api import (create_post_function, create_request_function,
                                              create_request_function_array)
log = logging.getLogger(__name__)


def create_consumer(config: Http):
    session: Optional[req.CustomSession] = None
    sim_counter: Optional[SimCounterConsumer] = None
    get_power: Optional[Callable] = None
    get_imported: Optional[Callable] = None
    get_exported: Optional[Callable] = None
    get_currents: Optional[Callable] = None
    get_temperatures: Optional[Callable] = None
    post_set_power_limit: Optional[Callable] = None
    post_switch_on: Optional[Callable] = None
    post_switch_off: Optional[Callable] = None

    def initializer():
        nonlocal session, sim_counter
        nonlocal get_power, get_imported, get_exported, get_currents, get_temperatures
        nonlocal post_set_power_limit, post_switch_on, post_switch_off
        if not config.configuration.url.startswith('https://'):
            raise ValueError("Only HTTPS URLs allowed for security")
        session = req.get_http_session()
        sim_counter = SimCounterConsumer(config.id, ComponentType.CONSUMER)

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
        # Authorization?
        post_switch_on(session, {"state": True})

    def switch_off():
        # Authorization?
        post_switch_off(session, {"state": False})

    def set_power_limit(power_limit: float, data: SetLimitData) -> None:
        # Authorization?
        post_set_power_limit(session, {"power_limit": power_limit})

    return ConfigurableConsumer(consumer_config=config,
                                initializer=initializer,
                                update=update,
                                set_power_limit=set_power_limit,
                                switch_on=switch_on,
                                switch_off=switch_off)


device_descriptor = DeviceDescriptor(configuration_factory=Http)
