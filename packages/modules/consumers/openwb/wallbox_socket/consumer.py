import logging
from typing import Any, Dict, Tuple

from paho.mqtt.client import Client, MQTTMessage

from control import data
from helpermodules.broker import BrokerClient
from helpermodules.pub import pub_single
from helpermodules.utils._get_default import get_default
from helpermodules.utils.topic_parser import decode_payload
from modules.common import req
from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_state import ConsumerState
from modules.common.configurable_consumer import ConfigurableConsumer
from modules.consumers.openwb.wallbox_socket.config import WallboxSocket

log = logging.getLogger(__name__)


def create_consumer(config: WallboxSocket) -> ConfigurableConsumer[WallboxSocket]:
    session = req.get_http_session()

    def clear_rfid() -> None:
        cp_type, host = get_connection()
        if cp_type != "openwb_pro":
            pub_single("openWB/set/internal_socket/data/last_tag", None, hostname=host)

    def get_connection() -> Tuple[str, str]:
        if config.configuration.chargepoint_id is None:
            return "internal_openwb", "localhost"
        try:
            cp_module = data.data.cp_data[f"cp{config.configuration.chargepoint_id}"].chargepoint_module
        except KeyError:
            raise KeyError(("Bitte einen vorhandenen openWB-Ladepunkt auswählen."))
        return cp_module.config.type, cp_module.config.configuration.ip_address

    def update() -> ConsumerState:
        cp_type, host = get_connection()
        if cp_type == "openwb_pro":
            return update_pro(host)
        return update_mqtt(host)

    def update_pro(host: str) -> ConsumerState:
        status = session.get(f"http://{host}/socket.php").json()
        if not status["socket_available"]:
            raise ValueError("In der ausgewählten openWB Pro ist keine Steckdose verbaut.")
        return ConsumerState(
            power=status["power"],
            powers=[status["power"], 0, 0],
            currents=[status["current"], 0, 0],
            voltages=[status["voltage"], 0, 0],
            imported=status["energy"],
            exported=0,
            state=status["socket_is_on"],
        )

    def update_mqtt(host: str) -> ConsumerState:
        received_topics: Dict[str, Any] = {}

        def parse_received_topics(value: str) -> Any:
            return received_topics.get(f"{prefix}{value}", get_default(ConsumerState, value))

        def on_connect(client: Client, userdata: Any, flags: Dict[str, int], rc: int) -> None:
            client.subscribe("openWB/internal_socket/get/#")

        def on_message(client: Client, userdata: Any, message: MQTTMessage) -> None:
            received_topics[message.topic] = decode_payload(message.payload)

        BrokerClient(f"subscribeWallboxSocketConsumer{config.id}", on_connect, on_message,
                     host=host, port=1886 if host == "localhost" else 1883).start_finite_loop(timeout=2)
        prefix = "openWB/internal_socket/get/"
        log.debug(f"Empfange MQTT Daten für Verbraucher {config.id}: {received_topics}")
        fault_state = received_topics.get(f"{prefix}fault_state")
        if fault_state == 2:
            consumer.fault_state.error(received_topics.get(
                f"{prefix}fault_str", "Fehlerstatus vom internen Ladepunkt"))
        elif fault_state == 1:
            consumer.fault_state.warning(received_topics.get(
                f"{prefix}fault_str", "Warnung vom internen Ladepunkt"))
        return ConsumerState(
            power=received_topics[f"{prefix}power"],
            imported=parse_received_topics("imported"),
            exported=parse_received_topics("exported"),
            powers=parse_received_topics("powers"),
            voltages=parse_received_topics("voltages"),
            currents=parse_received_topics("currents"),
            temperatures=parse_received_topics("temperatures"),
            state=parse_received_topics("state"),
            rfid=parse_received_topics("rfid"),
        )

    def switch(state: bool) -> None:
        cp_type, host = get_connection()
        if cp_type == "openwb_pro":
            session.post(f"http://{host}/socket.php", data={"socket_switch_on": int(state)})
        else:
            pub_single("openWB/set/internal_socket/data/set_state", state, hostname=host)

    consumer = ConfigurableConsumer(consumer_config=config,
                                    update=update,
                                    switch_on=lambda: switch(True),
                                    switch_off=lambda: switch(False),
                                    clear_rfid=clear_rfid)
    return consumer


device_descriptor = DeviceDescriptor(
    configuration_factory=WallboxSocket,
    compatibility_device_note=("Eine gleichzeitige Verwendung von Freischaltung per RFID und separater Leistunsmessung "
                               "ist nicht möglich."))
