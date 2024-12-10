#!/usr/bin/env python3
import logging
from typing import Dict, Tuple

from helpermodules import pub
from helpermodules.broker import BrokerClient
from helpermodules.utils.topic_parser import decode_payload
from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_state import IoState
from modules.common.configurable_io import ConfigurableIo
from modules.io_devices.add_on.config import AddOn

log = logging.getLogger(__name__)


def create_io(config: AddOn):
    def read() -> Tuple[bool, bool]:
        if config.configuration.host is None:
            raise ValueError("No host configured")
        return IoStateManager().get(config.configuration.host)

    def write(digital_output: Dict[int, int]):
        if config.configuration.host is None:
            raise ValueError("No host configured")
        pub.pub_single("openWB/set/io/states/local/set/digital_output", digital_output,
                       hostname=config.configuration.host)
        pub.pub_single(f"openWB/set/io/states/{config.id}/set/digital_output", digital_output)

    return ConfigurableIo(config=config, component_reader=read, component_writer=write)


device_descriptor = DeviceDescriptor(configuration_factory=AddOn)


class IoStateManager:
    def __init__(self) -> None:
        self.io_state = IoState()

    def get(self, host: str) -> IoState:
        BrokerClient("processBrokerBranch", self.on_connect, self.on_message, host,
                     1886 if host == "localhost" else 1883).start_finite_loop()
        return self.io_state

    def on_connect(self, client, userdata, flags, rc):
        """ connect to broker and subscribe to set topics
        """
        client.subscribe('openWB/io/states/local/#', 2)

    def on_message(self, client, userdata, msg):
        setattr(self.io_state, msg.topic.split("/")[-1], decode_payload(msg.payload))
