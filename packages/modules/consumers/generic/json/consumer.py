#!/usr/bin/env python3
import logging
from typing import Callable, Optional
import jq

from modules.common import req
from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_state import ConsumerState
from modules.common.component_type import ComponentType
from modules.common.configurable_consumer import ConfigurableConsumer
from modules.common.simcount._simcounter import SimCounterConsumer
from modules.consumers.generic.json.config import Json

log = logging.getLogger(__name__)


def create_consumer(config: Json):
    session = None
    sim_counter = None
    jq_power = None
    jq_imported = None
    jq_exported = None
    jq_currents = None
    jq_temperatures = None
    jq_set_power_limit = None
    jq_switch_on = None
    jq_switch_off = None

    def _compile_jq_filters() -> None:
        nonlocal jq_power, jq_imported, jq_exported, jq_currents, jq_temperatures
        jq_power = jq.compile(config.configuration.jq_power)
        jq_currents = [jq.compile(c) for c in config.configuration.jq_currents] if all(
            config.configuration.jq_currents) else None
        jq_imported = jq.compile(config.configuration.jq_imported) if config.configuration.jq_imported else None
        jq_exported = jq.compile(config.configuration.jq_exported) if config.configuration.jq_exported else None
        jq_temperatures = jq.compile(
            config.configuration.jq_temperatures) if config.configuration.jq_temperatures else None

    def create_post_function(path: Optional[str]) -> Callable[[dict], None]:
        nonlocal session
        if path is None:
            return lambda _: None
        else:
            def post_function(params: dict):
                session.post(config.configuration.url + path, json=params, timeout=5)
            return post_function

    def initializer():
        nonlocal session, sim_counter
        nonlocal jq_set_power_limit, jq_switch_on, jq_switch_off
        if not config.configuration.url.startswith('https://'):
            raise ValueError("Only HTTPS URLs allowed for security")
        session = req.get_http_session()
        sim_counter = SimCounterConsumer(config.id, ComponentType.CONSUMER)

        _compile_jq_filters()
        jq_set_power_limit = create_post_function(config.configuration.jq_set_power_limit)
        jq_switch_on = create_post_function(config.configuration.jq_switch_on)
        jq_switch_off = create_post_function(config.configuration.jq_switch_off)

    def update() -> None:
        nonlocal session, sim_counter, jq_power, jq_imported, jq_exported, jq_currents, jq_temperatures
        response = req.get_http_session().get(config.configuration.url, timeout=5).json()
        power = float(jq_power.input(response).first())
        temperatures = float(jq_temperatures.input(response).first()) if jq_temperatures is not None else None
        currents = ([float(j.input(response).first()) for j in jq_currents] if jq_currents is not None else None)
        if jq_imported is None or jq_exported is None:
            imported, exported = sim_counter.sim_count(power)
        else:
            imported = float(jq_imported.input(response).first())
            exported = float(jq_exported.input(response).first())

        return ConsumerState(
            power=power,
            currents=currents,
            imported=imported,
            exported=exported,
            temperatures=temperatures if isinstance(temperatures, list) else [temperatures],
        )

    def switch_on():
        nonlocal session, jq_switch_on
        # Authorization?
        jq_switch_on(session, params={"state": True})

    def switch_off():
        nonlocal session, jq_switch_off
        # Authorization?
        jq_switch_off(session, params={"state": False})

    def set_power_limit(power_limit: int):
        nonlocal session, jq_set_power_limit
        # Authorization?
        jq_set_power_limit(session, params={"power_limit": power_limit})

    return ConfigurableConsumer(consumer_config=config,
                                initializer=initializer,
                                update=update,
                                set_power_limit=set_power_limit,
                                switch_on=switch_on,
                                switch_off=switch_off)


device_descriptor = DeviceDescriptor(configuration_factory=Json)
