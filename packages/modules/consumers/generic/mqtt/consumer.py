#!/usr/bin/env python3
import logging

from helpermodules.broker import BrokerClient
from helpermodules.pub import Pub
from helpermodules.utils._get_default import get_default
from helpermodules.utils.topic_parser import decode_payload
from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_state import ConsumerState
from modules.common.configurable_consumer import ConfigurableConsumer
from modules.consumers.generic.mqtt.config import Mqtt

log = logging.getLogger(__name__)


def create_consumer(config: Mqtt):
    def update() -> None:
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
            return ConsumerState(
                power=received_topics[f"{topic_prefix}power"],
                imported=received_topics[f"{topic_prefix}imported"],
                exported=received_topics[f"{topic_prefix}exported"],
                powers=parse_received_topics("powers"),
                voltages=parse_received_topics("voltages"),
                currents=received_topics[f"{topic_prefix}currents"],
            )
        except KeyError:
            raise KeyError("Es wurden nicht alle notwendigen Daten empfangen.")

    def set_power_limit(power_limit: float) -> None:
        Pub().pub(f"openWB/mqtt/consumer/{config.id}/set/power_limit", power_limit)

    def switch_on() -> None:
        Pub().pub(f"openWB/mqtt/consumer/{config.id}/set/switch", True)

    def switch_off() -> None:
        Pub().pub(f"openWB/mqtt/consumer/{config.id}/set/switch", False)
    return ConfigurableConsumer(consumer_config=config,
                                update=update,
                                set_power_limit=set_power_limit,
                                switch_on=switch_on,
                                switch_off=switch_off)


device_descriptor = DeviceDescriptor(configuration_factory=Mqtt)
