import datetime
import logging
import paho.mqtt.client as mqtt
import time
from typing import Callable

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
        try:
            self.name = f"openWB-{name}-{get_name_suffix()}"
            self.client = mqtt.Client(self.name)
            self.client.on_connect = on_connect
            self.client.on_message = on_message
            self.client.connect(host, port)
        except Exception:
            log.exception("Fehler beim Abonnieren des internen Brokers")

    def start_infinite_loop(self) -> None:
        self.client.loop_forever()

    def start_finite_loop(self) -> None:
        self.client.loop_start()
        time.sleep(1)
        self.client.loop_stop()

    def disconnect(self) -> None:
        self.client.disconnect()
        log.info(f"Verbindung von Client {self.name} geschlossen.")


class InternalBrokerPublisher:
    def __init__(self) -> None:
        try:
            self.client = mqtt.Client(f"openWB-python-bulkpublisher-{get_name_suffix()}")
            self.client.connect("localhost", 1886)
        except Exception:
            log.exception("Fehler beim Verbindungsaufbau zum Bulkpublisher")

    def start_loop(self) -> None:
        self.client.loop_start()
