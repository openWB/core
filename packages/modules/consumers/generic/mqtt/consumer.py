#!/usr/bin/env python3
import logging
from typing import Optional

from helpermodules.broker import BrokerClient
from helpermodules.pub import Pub
from helpermodules.utils._get_default import get_default
from helpermodules.utils.topic_parser import decode_payload
from modules.common.abstract_consumer import CurrentValues
from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_state import ConsumerState
from modules.common.component_type import ComponentType
from modules.common.configurable_consumer import ConfigurableConsumer, SetLimitData
from modules.common.simcount._simcounter import SimCounterConsumer
from modules.consumers.generic.mqtt.config import Mqtt

log = logging.getLogger(__name__)


def create_consumer(config: Mqtt):
    sim_counter: Optional[SimCounterConsumer] = None

    def initializer() -> None:
        nonlocal sim_counter
        sim_counter = SimCounterConsumer(config.id, ComponentType.CONSUMER)

    def update() -> ConsumerState:
        def parse_received_topics(value: str):
            return received_topics.get(f"{topic_prefix}{value}", get_default(ConsumerState, value))

        def on_connect(client, userdata, flags, rc):
            client.subscribe(f"openWB/mqtt/consumer/{config.id}/get/#")

        def on_message(client, userdata, message):
            received_topics.update({message.topic: decode_payload(message.payload)})

        received_topics = {}
        BrokerClient(f"subscribeMqttConsumer{config.id}",
                     on_connect, on_message).start_finite_loop()

        log.debug(f"Empfange MQTT Daten für Verbraucher {config.id}: {received_topics}")
        topic_prefix = f"openWB/mqtt/consumer/{config.id}/get/"
        try:
            power = received_topics[f"{topic_prefix}power"]
            imported = parse_received_topics("imported")
            exported = parse_received_topics("exported")
            if imported is None or exported is None:
                imported, exported = sim_counter.sim_count(power)

            return ConsumerState(
                power=power,
                imported=imported,
                exported=exported,
                powers=parse_received_topics("powers"),
                voltages=parse_received_topics("voltages"),
                currents=parse_received_topics("currents"),
                temperatures=parse_received_topics("temperatures"),
            )
        except KeyError:
            raise KeyError("Es wurden nicht alle notwendigen Daten empfangen.")

    def set_power_limit(power_limit: float, data: SetLimitData) -> None:
        Pub().pub(f"openWB/set/mqtt/consumer/{config.id}/set/power", power_limit)

    def switch_on() -> None:
        Pub().pub(f"openWB/set/mqtt/consumer/{config.id}/set/switch", True)

    def switch_off() -> None:
        Pub().pub(f"openWB/set/mqtt/consumer/{config.id}/set/switch", False)

    def send_values(values: CurrentValues) -> None:
        Pub().pub(f"openWB/set/mqtt/consumer/{config.id}/set/bat_power", values.bat_power)
        Pub().pub(f"openWB/set/mqtt/consumer/{config.id}/set/bat_soc", values.bat_soc)
        Pub().pub(f"openWB/set/mqtt/consumer/{config.id}/set/cp_power", values.cp_power)
        Pub().pub(f"openWB/set/mqtt/consumer/{config.id}/set/evu_power", values.evu_power)
        Pub().pub(f"openWB/set/mqtt/consumer/{config.id}/set/home_consumption", values.home_consumption)
        Pub().pub(f"openWB/set/mqtt/consumer/{config.id}/set/pv_power", values.pv_power)

    return ConfigurableConsumer(consumer_config=config,
                                initializer=initializer,
                                update=update,
                                send_values=send_values,
                                set_power_limit=set_power_limit,
                                switch_on=switch_on,
                                switch_off=switch_off)


device_descriptor = DeviceDescriptor(configuration_factory=Mqtt)
