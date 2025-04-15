#!/usr/bin/env python3
from typing import Iterable, Union
import logging

from helpermodules.broker import BrokerClient
from helpermodules.utils.topic_parser import decode_payload
from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_type import type_to_topic_mapping
from modules.common.configurable_device import ComponentFactoryByType, ConfigurableDevice, MultiComponentUpdater
from modules.devices.generic.mqtt import bat, counter, inverter
from modules.devices.generic.mqtt.config import Mqtt, MqttBatSetup, MqttCounterSetup, MqttInverterSetup

log = logging.getLogger(__name__)


def create_device(device_config: Mqtt):
    def create_bat_component(component_config: MqttBatSetup):
        return bat.MqttBat(component_config, device_id=device_config.id)

    def create_counter_component(component_config: MqttCounterSetup):
        return counter.MqttCounter(component_config, device_id=device_config.id)

    def create_inverter_component(component_config: MqttInverterSetup):
        return inverter.MqttInverter(component_config, device_id=device_config.id)

    def update_components(components: Iterable[Union[bat.MqttBat, counter.MqttCounter, inverter.MqttInverter]]):
        def on_connect(client, userdata, flags, rc):
            for component in components:
                client.subscribe(f"openWB/mqtt/{type_to_topic_mapping(component.component_config.type)}/"
                                 f"{component.component_config.id}/#")

        def on_message(client, userdata, message):
            received_topics.update({message.topic: decode_payload(message.payload)})

        received_topics = {}
        BrokerClient(f"subscribeMqttDevice{device_config.id}", on_connect, on_message).start_finite_loop()

        if received_topics:
            log.debug(f"Empfange MQTT Daten für Gerät {device_config.id}: {received_topics}")
            for component in components:
                component.update(received_topics)
        else:
            raise Exception(
                f"Keine MQTT-Daten für Gerät {device_config.id} empfangen oder es werden veraltete Topics"
                " verwendet. Diese funktionieren mit Einschränkungen trotz dieser Fehlermeldung. Bitte die Doku in "
                "den Einstellungen beachten.")

    return ConfigurableDevice(
        device_config=device_config,
        component_factory=ComponentFactoryByType(
            bat=create_bat_component,
            counter=create_counter_component,
            inverter=create_inverter_component,
        ),
        component_updater=MultiComponentUpdater(update_components)
    )


device_descriptor = DeviceDescriptor(configuration_factory=Mqtt)
