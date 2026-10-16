import datetime
import errno
import logging
import paho.mqtt.client as mqtt
import threading
import time
from typing import Any, Callable, Dict, List, Tuple

from helpermodules.utils.topic_parser import decode_payload

log = logging.getLogger(__name__)

# Zeitfenster nach dem ersten Verbindungsversuch, in dem "noch nicht verbunden" nicht als Fehler
# gilt: connect_async()/loop_start() verbinden im Hintergrund, is_connected() ist direkt danach
# so gut wie immer noch False. Ohne Kulanzfrist würde der allererste publish() an einen neuen Host
# nach jedem Neustart praktisch garantiert einen falschen Fehler auslösen.
INITIAL_CONNECT_GRACE = 5.0


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

    def start_finite_loop(self, timeout: float = 1) -> None:
        self.client.loop_start()
        time.sleep(timeout)
        self.client.loop_stop()

    def disconnect(self) -> None:
        self.client.disconnect()
        log.info(f"Verbindung von Client {self.name} geschlossen.")


class PersistentBrokerClient:
    """Lang lebende, automatisch wiederverbindende MQTT-Verbindung zu einem Host (typischerweise ein
    Secondary-openWB), die über mehrere Regelzyklen hinweg wiederverwendet wird.

    Ersetzt für publish/subscribe zu externen Hosts das bisherige Muster "pro Aufruf neu verbinden,
    kurz warten, wieder trennen" (paho publish.single() bzw. BrokerClient.start_finite_loop()): jeder
    dieser Auf- und Abbauten ist ein eigener TCP+MQTT-Handshake, und mehrere davon pro Regelzyklus
    (z.B. 5x publish + 1x subscribe für einen externen Ladepunkt) mussten bisher gemeinsam in das enge
    Timeout von control_interval/3 passen - schon normaler Netzwerk-Jitter zur Gegenstelle konnte das
    reißen. Mit einer dauerhaft offenen, im Hintergrund automatisch wiederverbundenen Verbindung fällt
    dieser Auf-/Abbau pro Zyklus komplett weg.
    """

    def __init__(self, host: str, port: int) -> None:
        self.host = host
        self.port = port
        self._lock = threading.Lock()
        self._subscribed_topics: set = set()
        self._received_topics: Dict[str, Any] = {}
        # eigenes Event je wartendem Aufrufer statt eines gemeinsamen: bei zwei Ladepunkten am selben
        # Host (duo_num 0/1, gemeinsame Verbindung) laufen mehrere wait_for_fresh_data()-Aufrufe
        # gleichzeitig auf demselben PersistentBrokerClient - ein gemeinsames Event hätte dazu geführt,
        # dass ein Aufrufer das Event im eigenen clear() dem anderen wegnimmt (verpasster Wakeup).
        self._waiters: List[threading.Event] = []
        self._ever_connected = False
        self._created_at = time.monotonic()
        self.client = mqtt.Client(f"openWB-persistent-{host}-{port}-{get_name_suffix()}")
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.reconnect_delay_set(min_delay=1, max_delay=30)
        try:
            self.client.connect_async(host, port)
            self.client.loop_start()
        except Exception:
            log.exception(f"Fehler beim Verbindungsaufbau zu {host}:{port}")

    def _on_connect(self, client, userdata, flags, rc) -> None:
        self._ever_connected = True
        with self._lock:
            topics = list(self._subscribed_topics)
        for topic in topics:
            client.subscribe(topic)

    def _on_message(self, client, userdata, message) -> None:
        with self._lock:
            self._received_topics[message.topic] = decode_payload(message.payload)
            waiters = list(self._waiters)
        for waiter in waiters:
            waiter.set()

    def publish(self, topic: str, payload, qos: int = 0, retain: bool = True) -> None:
        # anders als paho publish.single() wirft Client.publish() bei fehlender Verbindung keine Exception,
        # sondern liefert nur einen Fehlercode zurueck - hier bewusst in eine Exception uebersetzt, damit
        # Aufrufer (insbesondere ErrorTimerContext/client_error_context) eine nicht erreichbare Gegenstelle
        # weiterhin wie bisher als Fehler erkennen und nach 60s die Sicherheitsabschaltung greifen kann.
        if not self.client.is_connected():
            if not self._ever_connected and time.monotonic() - self._created_at < INITIAL_CONNECT_GRACE:
                # Erstverbindung läuft im Hintergrund noch (siehe INITIAL_CONNECT_GRACE weiter oben) -
                # das ist kein Fehlerfall, Nachricht wird verworfen, naechster Zyklus greift wieder.
                return
            # errno.EHOSTUNREACH statt nur einer Nachricht, damit der bestehende OSError-Handler
            # (helpermodules/exceptions/os.py) die schon vorhandene, uebersetzte Meldung "Die Verbindung
            # zum Host ist fehlgeschlagen..." verwendet, statt auf "Unbekannter Fehler" zurueckzufallen -
            # der greift nur ueber e.errno/e.strerror, eine reine Textnachricht wuerde er ignorieren.
            raise ConnectionError(errno.EHOSTUNREACH, f"Keine Verbindung zu {self.host}:{self.port}")
        self.client.publish(topic, payload, qos=qos, retain=retain)

    def ensure_subscribed(self, topic_filter: str) -> None:
        with self._lock:
            if topic_filter in self._subscribed_topics:
                return
            self._subscribed_topics.add(topic_filter)
        self.client.subscribe(topic_filter)

    def wait_for_fresh_data(self, max_wait: float = 2.0, settle: float = 0.1) -> Dict[str, Any]:
        """Wartet auf mindestens eine neue Nachricht und danach auf eine kurze Ruhephase ohne weitere
        Nachrichten (Sammeln des restlichen Nachrichten-Schwalls, z.B. alle retained Topics nach einem
        Reconnect), insgesamt begrenzt auf `max_wait`. Liefert bei mindestens einer neuen Nachricht den
        gesamten aktuellen Stand aller je empfangenen Topics zurück (nicht nur die seit dem Aufruf neu
        eingetroffenen) - sonst ein leeres Dict, damit Aufrufer "keine aktuellen Daten diesen Zyklus"
        weiterhin wie bisher von "Daten vorhanden" unterscheiden können (z.B. für Fault-State-Meldungen)."""
        waiter = threading.Event()
        with self._lock:
            self._waiters.append(waiter)
        try:
            deadline = time.monotonic() + max_wait
            if not waiter.wait(timeout=max(0.0, deadline - time.monotonic())):
                return {}
            while True:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    break
                waiter.clear()
                if not waiter.wait(timeout=min(settle, remaining)):
                    break
            with self._lock:
                return dict(self._received_topics)
        finally:
            with self._lock:
                self._waiters.remove(waiter)


_persistent_clients: Dict[Tuple[str, int], PersistentBrokerClient] = {}
_persistent_clients_lock = threading.Lock()


def get_persistent_broker_client(host: str, port: int) -> PersistentBrokerClient:
    key = (host, port)
    with _persistent_clients_lock:
        client = _persistent_clients.get(key)
        if client is None:
            client = PersistentBrokerClient(host, port)
            _persistent_clients[key] = client
        return client


class InternalBrokerPublisher:
    def __init__(self) -> None:
        try:
            self.client = mqtt.Client(f"openWB-python-bulk-publisher-{get_name_suffix()}")
            self.client.connect("localhost", 1886)
        except Exception:
            log.exception("Fehler beim Verbindungsaufbau zum Bulk-Publisher")

    def start_loop(self) -> None:
        self.client.loop_start()
