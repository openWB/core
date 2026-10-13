import logging
import time

from control import data
from helpermodules.broker import BrokerClient
from helpermodules.pub import pub_single
from helpermodules.utils._get_default import get_default
from helpermodules.utils.topic_parser import decode_payload
from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_state import ConsumerState
from modules.common.configurable_consumer import ConfigurableConsumer
from modules.consumers.openwb.wall_socket.config import WallSocket

log = logging.getLogger(__name__)


def create_consumer(config: WallSocket):
    def get_host():
        cp_module = data.data.cp_data[f"cp{config.configuration.chargepoint_id}"].chargepoint_module
        if cp_module.config.type == "internal_openwb":
            return "localhost"
        else:
            return cp_module.config.configuration.ip_address

    def update():
        pub_single("openWB/set/internal_socket/data/heartbeat", time.time(), hostname=get_host())
        received_topics = {}

        def parse_received_topics(value: str):
            return received_topics.get(f"{prefix}{value}", get_default(ConsumerState, value))

        def on_connect(client, userdata, flags, rc):
            client.subscribe("openWB/internal_socket/get/#")

        def on_message(client, userdata, message):
            received_topics[message.topic] = decode_payload(message.payload)

        BrokerClient(f"subscribeSocketConsumer{config.id}", on_connect, on_message,
                     host=get_host(), port=1883).start_finite_loop(timeout=2)
        prefix = "openWB/internal_socket/get/"
        log.debug(f"Empfange MQTT Daten für Verbraucher {config.id}: {received_topics}")
        try:
            fault_state = received_topics.get(f"{prefix}fault_state")
            if fault_state == 2:
                consumer.fault_state.error(received_topics.get(
                    f"{prefix}fault_str", "Fehlerstatus vom internen Ladepunkt"))
            elif fault_state == 1:
                consumer.fault_state.warning(received_topics.get(
                    f"{prefix}fault_str", "Warnung vom internen Ladepunkt"))
            return ConsumerState(
                power=parse_received_topics("power"),
                imported=parse_received_topics("imported"),
                exported=parse_received_topics("exported"),
                powers=parse_received_topics("powers"),
                voltages=parse_received_topics("voltages"),
                currents=parse_received_topics("currents"),
                temperatures=parse_received_topics("temperatures"),
            )
        except KeyError:
            raise KeyError("Es wurden nicht alle notwendigen Daten empfangen.")

    def switch(state):
        pub_single("openWB/set/internal_socket/data/set_state", state, hostname=get_host())
        pub_single("openWB/set/internal_socket/data/heartbeat", time.time(), hostname=get_host())

    consumer = ConfigurableConsumer(consumer_config=config,
                                    update=update,
                                    switch_on=lambda: switch(True),
                                    switch_off=lambda: switch(False))
    return consumer


device_descriptor = DeviceDescriptor(configuration_factory=WallSocket)
