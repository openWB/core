#!/usr/bin/env python3

import logging

from helpermodules.broker import BrokerClient
from helpermodules.utils.topic_parser import decode_payload
from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_state import IoState
from modules.common.configurable_io import ConfigurableIo
from modules.io_devices.load_manager.config import AnalogInputMapping
from modules.io_devices.load_manager.config import LoadManager

log = logging.getLogger(__name__)
control_command_log = logging.getLogger("steuve_control_command")


def create_io(config: LoadManager):
    received_topics = {}
    broker = None

    def read():
        broker.start_finite_loop()
        log.debug(f"Empfange MQTT Daten für LoadManager {config.id}: {received_topics}")
        io_state = IoState()
        io_state.analog_input = getattr(io_state, "analog_input", None) or {}
        io_state.analog_output = getattr(io_state, "analog_output", None) or {}
        io_state.digital_input = getattr(io_state, "digital_input", None) or {}
        io_state.digital_output = getattr(io_state, "digital_output", None) or {}

        if received_topics.get("openWB/mqtt/loadmanager/set/loadmanager"):
            payload = received_topics["openWB/mqtt/loadmanager/set/loadmanager"]
            io_state.analog_input.update({AnalogInputMapping.MAX_POWER.name: payload["max_power"]})
            io_state.analog_input.update({AnalogInputMapping.MAX_CURRENT.name: payload["max_current"]})
            io_state.analog_input.update({AnalogInputMapping.TIMESTAMP.name: payload["timestamp"]})
        return io_state

    def initializer():
        nonlocal broker
        nonlocal received_topics

        def on_connect(client, userdata, flags, rc):
            client.subscribe("openWB/mqtt/loadmanager/#")

        def on_message(client, userdata, message):
            received_topics.update({message.topic: decode_payload(message.payload)})

        received_topics = {}
        broker = BrokerClient("subscribeMqttLoadmanager",
                              on_connect, on_message)

    return ConfigurableIo(config=config, component_reader=read, component_writer=lambda: None, initializer=initializer)


device_descriptor = DeviceDescriptor(configuration_factory=LoadManager)
