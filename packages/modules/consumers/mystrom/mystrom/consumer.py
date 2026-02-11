#!/usr/bin/env python3
from pymodbus.constants import Endian
import logging
from modules.common import req
from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_state import ConsumerState
from modules.common.component_type import ComponentType
from modules.common.configurable_consumer import ConfigurableConsumer
from modules.common.modbus import ModbusDataType, ModbusTcpClient_
from modules.common.simcount._simcounter import SimCounterConsumer
from modules.consumers.mystrom.mystrom.config import MyStrom

log = logging.getLogger(__name__)


def create_consumer(config: MyStrom):
    session = None
    sim_counter = None

    def initializer():
        nonlocal session, sim_counter
        session = req.get_http_session()
        sim_counter = SimCounterConsumer(config.id, ComponentType.CONSUMER)

    def error_handler() -> None:
        initializer()

    def update() -> ConsumerState:
        nonlocal session, sim_counter
        resp = session.get(f"http://{config.configuration.ip_address}/report", timeout=3).json()
        power = resp["power"]
        relais = resp["relay"]
        temp = float(resp["temperature"])
        imported, exported = sim_counter.sim_count(power)
        return ConsumerState(
            power=power,
            imported=imported,
            exported=exported,
            temperatures=[temp],
            state=relais
        )

    def switch_on() -> None:
        nonlocal session
        session.get(f"http://{config.configuration.ip_address}/relay?state=1", timeout=3)

    def switch_off() -> None:
        nonlocal session
        session.get(f"http://{config.configuration.ip_address}/relay?state=0", timeout=3)

    return ConfigurableConsumer(consumer_config=config,
                                initializer=initializer,
                                error_handler=error_handler,
                                update=update,
                                switch_on=switch_on,
                                switch_off=switch_off,
                                )


device_descriptor = DeviceDescriptor(configuration_factory=MyStrom)
