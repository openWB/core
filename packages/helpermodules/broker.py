import datetime
import errno
import logging
import paho.mqtt.client as mqtt
import threading
import time
from typing import Any, Callable, Dict, List

from helpermodules.utils.topic_parser import decode_payload

log = logging.getLogger(__name__)


def get_name_suffix() -> str:
    with open('/proc/cpuinfo', 'r') as f:
        for line in f:
            if line[0:6] == 'Serial':
                serial = line[10:26]
        serial = "0000000000000000"
    return f"{serial}-{datetime.datetime.today().timestamp()}"


class BrokerClient:
    def __init__(self,
                 name: str,
                 on_connect: Callable,
                 on_message: Callable,
                 host: str = "localhost",
                 port: int = 1886) -> None:
        self.client = None
        try:
            self.name = f"openWB-{name}-{get_name_suffix()}"
            # Try to create client with paho-mqtt 2.0+ API first (requires callback_api_version)
            try:
                self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, self.name)
            except TypeError:
                # Fall back to older paho-mqtt API
                self.client = mqtt.Client(self.name)
            self.client.on_connect = on_connect
            self.client.on_message = on_message
            self.client.connect(host, port)
        except Exception:
            log.exception("Fehler beim Abonnieren des internen Brokers")

    def start_infinite_loop(self) -> None:
        if self.client:
            self.client.loop_forever()

    def start_finite_loop(self, timeout: float = 1) -> None:
        if self.client:
            self.client.loop_start()
            time.sleep(timeout)
            self.client.loop_stop()

    def disconnect(self) -> None:
        if self.client:
            self.client.disconnect()
            log.info(f"Verbindung von Client {self.name} geschlossen.")


def publish_and_collect(host: str,
                        port: int,
                        messages: List[Dict[str, Any]],
                        topic_filter: str,
                        is_complete: Callable[[Dict[str, Any]], bool],
                        timeout: float = 2,
                        settle: float = 0.1,
                        name: str = "publishAndCollect") -> Dict[str, Any]:
    """ Sendet Nachrichten und sammelt anschließend die Topics eines Filters über eine einzige Verbindung.

    Die Verbindung wird nur für diesen Aufruf aufgebaut. Gewartet wird nur so lange, bis `is_complete` die
    empfangenen Topics als vollständig bewertet. Danach wird weiter gesammelt, bis `settle` Sekunden lang keine
    Nachricht mehr eingegangen ist (Ende der retained Topics), höchstens aber `timeout` Sekunden insgesamt.
    Was als vollständig gilt, entscheidet der Aufrufer.

    Parameter
    ---------
    messages: Nachrichten als paho-Dict (topic, payload, qos, retain)
    topic_filter: Filter, der abonniert wird
    is_complete: bekommt die bisher empfangenen Topics (Topic -> Payload)
    name: Teil der Client-ID; muss je gleichzeitig laufendem Aufrufer an denselben Broker eindeutig sein, da der
          Broker bei gleicher Client-ID die ältere Verbindung trennt
    Rückgabe: empfangene Topics; leer, wenn nichts empfangen wurde

    Raises
    ------
    OSError: Verbindung konnte nicht aufgebaut werden oder Nachrichten konnten nicht gesendet werden
    """
    connected = threading.Event()
    connect_result: List[int] = []
    received: Dict[str, Any] = {}
    condition = threading.Condition()
    last_message_time = time.monotonic()

    def on_connect(client, userdata, flags, rc):
        connect_result.append(rc)
        if rc == 0:
            client.subscribe(topic_filter)
        connected.set()

    def on_message(client, userdata, message):
        nonlocal last_message_time
        with condition:
            last_message_time = time.monotonic()
            received[message.topic] = decode_payload(message.payload)
            condition.notify_all()

    client = mqtt.Client(f"openWB-{name}-{get_name_suffix()}")
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(host, port)
    deadline = time.monotonic() + timeout
    client.loop_start()
    try:
        if not connected.wait(timeout=timeout) or connect_result[-1] != 0:
            raise ConnectionError(errno.EHOSTUNREACH, f"Keine Verbindung zu {host}:{port} aufgebaut")
        try:
            infos = [client.publish(message["topic"], message["payload"], qos=message["qos"],
                                    retain=message["retain"]) for message in messages]
            for info in infos:
                info.wait_for_publish(timeout=max(0.0, deadline - time.monotonic()))
        except RuntimeError as e:
            raise ConnectionError(errno.EHOSTUNREACH, f"Nachrichten an {host}:{port} nicht gesendet: {e}")
        if not all(info.is_published() for info in infos):
            raise ConnectionError(errno.EHOSTUNREACH, f"Nachrichten an {host}:{port} nicht rechtzeitig gesendet")
        with condition:
            while not is_complete(received):
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    break
                condition.wait(remaining)
            while is_complete(received):
                now = time.monotonic()
                wait_time = min(deadline - now, last_message_time + settle - now)
                if wait_time <= 0:
                    break
                condition.wait(wait_time)
            return dict(received)
    finally:
        client.disconnect()
        client.loop_stop()


class InternalBrokerPublisher:
    def __init__(self) -> None:
        self.client = None
        try:
            # Try to create client with paho-mqtt 2.0+ API first (requires callback_api_version)
            try:
                self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1,
                                          f"openWB-python-bulk-publisher-{get_name_suffix()}")
            except TypeError:
                # Fall back to older paho-mqtt API
                self.client = mqtt.Client(f"openWB-python-bulk-publisher-{get_name_suffix()}")
            self.client.connect("localhost", 1886)
        except Exception:
            log.exception("Fehler beim Verbindungsaufbau zum Bulk-Publisher")

    def start_loop(self) -> None:
        if self.client:
            self.client.loop_start()
