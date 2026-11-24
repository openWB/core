import errno
import threading
import time
from unittest.mock import Mock

import pytest

from helpermodules import broker

MESSAGES = [{"topic": "openWB/set/a", "payload": "1", "qos": 0, "retain": True},
            {"topic": "openWB/set/b", "payload": "2", "qos": 0, "retain": True}]


class FakeClient:
    """Verhält sich wie paho, ruft on_connect/on_message aus einem eigenen Thread auf."""
    instance = None
    instances = []

    def __init__(self, client_id="", rc: int = 0, connack: bool = True, incoming=(), published: bool = True):
        self.client_id = client_id
        self.rc = rc
        self.connack = connack
        self.incoming = list(incoming)
        self.published = published
        self.calls = []
        self.on_connect = None
        self.on_message = None
        FakeClient.instance = self
        FakeClient.instances.append(self)

    def connect(self, host, port):
        self.calls.append(("connect", host, port))

    def loop_start(self):
        self.calls.append(("loop_start",))
        if self.connack:
            threading.Thread(target=self.on_connect, args=(self, None, {}, self.rc)).start()

    def subscribe(self, topic_filter):
        self.calls.append(("subscribe", topic_filter))
        for delay, topic, payload in self.incoming:
            threading.Timer(delay, self.on_message, args=(self, None, Mock(topic=topic, payload=payload))).start()

    def publish(self, topic, payload, qos, retain):
        self.calls.append(("publish", topic, payload))
        info = Mock()
        info.is_published.return_value = self.published
        return info

    def disconnect(self):
        self.calls.append(("disconnect",))

    def loop_stop(self):
        self.calls.append(("loop_stop",))


@pytest.fixture
def fake_client(monkeypatch):
    FakeClient.instances = []

    def install(**kwargs):
        monkeypatch.setattr(broker.mqtt, "Client", lambda client_id: FakeClient(client_id, **kwargs))
        return FakeClient
    return install


def names(client):
    return [call[0] for call in client.calls]


def test_publishes_all_messages_over_one_connection_and_returns_complete_data(fake_client):
    fake_client(incoming=[(0.0, "x/get/power", b"100"), (0.0, "x/get/currents", b"[1, 2, 3]")])

    received = broker.publish_and_collect(
        "10.0.0.5", 1883, MESSAGES, "x/get/#", lambda topics: len(topics) == 2, timeout=1, settle=0.01)

    client = FakeClient.instance
    assert received == {"x/get/power": 100, "x/get/currents": [1, 2, 3]}
    assert names(client).count("connect") == 1
    assert ("connect", "10.0.0.5", 1883) in client.calls
    assert ("subscribe", "x/get/#") in client.calls
    assert [c[1] for c in client.calls if c[0] == "publish"] == ["openWB/set/a", "openWB/set/b"]
    assert names(client)[-2:] == ["disconnect", "loop_stop"]


def test_returns_as_soon_as_data_is_complete(fake_client):
    fake_client(incoming=[(0.0, "x/get/power", b"100")])
    start = time.monotonic()

    received = broker.publish_and_collect(
        "10.0.0.5", 1883, MESSAGES, "x/get/#", lambda topics: "x/get/power" in topics, timeout=5, settle=0.01)

    assert received == {"x/get/power": 100}
    assert time.monotonic() - start < 1


def test_collects_topics_arriving_within_settle_time(fake_client):
    fake_client(incoming=[(0.0, "x/get/power", b"100"), (0.05, "x/get/soc", b"80")])

    received = broker.publish_and_collect(
        "10.0.0.5", 1883, MESSAGES, "x/get/#", lambda topics: "x/get/power" in topics, timeout=1, settle=0.3)

    assert received == {"x/get/power": 100, "x/get/soc": 80}


def test_keeps_collecting_while_messages_keep_arriving_within_settle_time(fake_client):
    fake_client(incoming=[(0.0, "x/get/power", b"100"), (0.06, "x/get/soc", b"80"),
                          (0.12, "x/get/rfid", b'"abc"'), (0.18, "x/get/version", b'"1.0"')])

    received = broker.publish_and_collect(
        "10.0.0.5", 1883, MESSAGES, "x/get/#", lambda topics: "x/get/power" in topics, timeout=2, settle=0.1)

    assert set(received) == {"x/get/power", "x/get/soc", "x/get/rfid", "x/get/version"}


def test_collecting_after_complete_data_is_limited_by_timeout(fake_client):
    fake_client(incoming=[(i * 0.03, f"x/get/t{i}", b"1") for i in range(40)])
    start = time.monotonic()

    received = broker.publish_and_collect(
        "10.0.0.5", 1883, MESSAGES, "x/get/#", lambda topics: "x/get/t0" in topics, timeout=0.3, settle=0.1)

    assert time.monotonic() - start < 0.6
    assert "x/get/t0" in received
    assert len(received) < 40


def test_returns_partial_data_after_timeout(fake_client):
    fake_client(incoming=[(0.0, "x/get/power", b"100")])

    received = broker.publish_and_collect(
        "10.0.0.5", 1883, MESSAGES, "x/get/#", lambda topics: len(topics) == 2, timeout=0.2, settle=0.01)

    assert received == {"x/get/power": 100}


def test_returns_empty_dict_without_data(fake_client):
    fake_client()

    received = broker.publish_and_collect(
        "10.0.0.5", 1883, MESSAGES, "x/get/#", lambda topics: bool(topics), timeout=0.1, settle=0.01)

    assert received == {}


@pytest.mark.parametrize("kwargs", [
    pytest.param({"connack": False}, id="no connack"),
    pytest.param({"rc": 5}, id="connection refused by broker"),
])
def test_raises_when_connection_is_not_established(fake_client, kwargs):
    fake_client(**kwargs)

    with pytest.raises(ConnectionError) as excinfo:
        broker.publish_and_collect("10.0.0.5", 1883, MESSAGES, "x/get/#", lambda topics: True, timeout=0.1)

    client = FakeClient.instance
    assert excinfo.value.errno == errno.EHOSTUNREACH
    assert "publish" not in names(client)
    assert names(client)[-2:] == ["disconnect", "loop_stop"]


def test_raises_when_messages_were_not_sent(fake_client):
    fake_client(published=False)

    with pytest.raises(ConnectionError) as excinfo:
        broker.publish_and_collect("10.0.0.5", 1883, MESSAGES, "x/get/#", lambda topics: True, timeout=0.1)

    assert excinfo.value.errno == errno.EHOSTUNREACH
    assert names(FakeClient.instance)[-2:] == ["disconnect", "loop_stop"]


def test_connection_error_is_translated_to_host_unreachable_message():
    from helpermodules.exceptions.os import handle_os_error
    error = ConnectionError(errno.EHOSTUNREACH, "Keine Verbindung")

    assert handle_os_error(error) == "Die Verbindung zum Host ist fehlgeschlagen. Überprüfe Adresse und Netzwerk."


def test_concurrent_calls_for_two_chargepoints_of_one_secondary_do_not_share_state(monkeypatch):
    """Duo: beide Ladepunkte rufen gleichzeitig denselben Secondary ab. Jeder Aufruf hat eigene Verbindung,
    eigenes Abo, eigene Empfangsdaten und eine eigene Client-ID."""
    FakeClient.instances = []
    incoming = {"x/0/get/#": [(0.0, "x/0/get/power", b"100"), (0.02, "x/0/get/rfid", b'"a"')],
                "x/1/get/#": [(0.0, "x/1/get/power", b"200"), (0.02, "x/1/get/rfid", b'"b"')]}
    created = []

    def create(client_id):
        client = FakeClient(client_id)
        created.append(client)
        original_subscribe = client.subscribe
        client.subscribe = lambda topic_filter: (setattr(client, "incoming", incoming[topic_filter]),
                                                 original_subscribe(topic_filter))
        return client

    monkeypatch.setattr(broker.mqtt, "Client", create)
    results = {}

    def collect(duo_num):
        results[duo_num] = broker.publish_and_collect(
            "10.0.0.5", 1883, MESSAGES, f"x/{duo_num}/get/#",
            lambda topics: f"x/{duo_num}/get/power" in topics, timeout=1, settle=0.1,
            name=f"subscribeSeriesChargepoint{5 + duo_num}")

    threads = [threading.Thread(target=collect, args=(duo_num,)) for duo_num in (0, 1)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert results[0] == {"x/0/get/power": 100, "x/0/get/rfid": "a"}
    assert results[1] == {"x/1/get/power": 200, "x/1/get/rfid": "b"}
    assert len({client.client_id for client in created}) == 2
    assert all("subscribeSeriesChargepoint" in client.client_id for client in created)
