import errno
import threading
import time
from unittest.mock import MagicMock, patch

import pytest

from helpermodules import broker
from helpermodules.exceptions.os import handle_os_error
from helpermodules.broker import PersistentBrokerClient, get_persistent_broker_client


@pytest.fixture
def mock_mqtt_client():
    with patch("helpermodules.broker.mqtt.Client") as mock_client_cls:
        instance = MagicMock()
        instance.is_connected.return_value = True
        mock_client_cls.return_value = instance
        yield instance


class TestPersistentBrokerClient:
    def test_publish_does_not_raise_during_initial_connect_grace_period(self, mock_mqtt_client):
        """connect_async()/loop_start() verbinden im Hintergrund - direkt nach dem Konstruktor ist
        is_connected() so gut wie immer noch False, ohne dass das ein echter Fehler waere (siehe
        Review-Kommentar zu PR #3996: der allererste publish() an einen neuen Host loeste sonst nach
        jedem Neustart praktisch garantiert einen falschen Fehler aus)."""
        mock_mqtt_client.is_connected.return_value = False
        client = PersistentBrokerClient("10.0.0.5", 1883)

        client.publish("some/topic", "1")

        mock_mqtt_client.publish.assert_not_called()

    def test_publish_raises_once_initial_connect_grace_period_expires(self, mock_mqtt_client):
        mock_mqtt_client.is_connected.return_value = False
        client = PersistentBrokerClient("10.0.0.5", 1883)
        client._created_at -= broker.INITIAL_CONNECT_GRACE + 1

        with pytest.raises(ConnectionError) as excinfo:
            client.publish("some/topic", "1")

        mock_mqtt_client.publish.assert_not_called()
        # errno muss gesetzt sein, sonst faellt der bestehende OSError-Handler
        # (helpermodules/exceptions/os.py) auf die nichtssagende "Unbekannter Fehler"-Meldung zurueck,
        # statt die schon vorhandene, uebersetzte "Verbindung zum Host fehlgeschlagen"-Meldung zu nutzen.
        assert excinfo.value.errno == errno.EHOSTUNREACH
        assert handle_os_error(excinfo.value) == (
            "Die Verbindung zum Host ist fehlgeschlagen. Überprüfe Adresse und Netzwerk.")

    def test_publish_raises_immediately_once_connection_has_dropped(self, mock_mqtt_client):
        """Eine Verbindung, die schon einmal stand und dann abbricht, ist ein echter Ausfall - dafuer
        gibt es keine Kulanzfrist, das muss weiterhin sofort erkannt werden."""
        client = PersistentBrokerClient("10.0.0.5", 1883)
        client._on_connect(mock_mqtt_client, None, None, 0)
        mock_mqtt_client.is_connected.return_value = False

        with pytest.raises(ConnectionError):
            client.publish("some/topic", "1")

    def test_publish_forwards_when_connected(self, mock_mqtt_client):
        client = PersistentBrokerClient("10.0.0.5", 1883)

        client.publish("some/topic", "1", qos=0, retain=True)

        mock_mqtt_client.publish.assert_called_once_with("some/topic", "1", qos=0, retain=True)

    def test_ensure_subscribed_is_idempotent(self, mock_mqtt_client):
        client = PersistentBrokerClient("10.0.0.5", 1883)

        client.ensure_subscribed("openWB/internal_chargepoint/0/get/#")
        client.ensure_subscribed("openWB/internal_chargepoint/0/get/#")
        client.ensure_subscribed("openWB/internal_chargepoint/1/get/#")

        assert mock_mqtt_client.subscribe.call_count == 2

    def test_on_connect_resubscribes_all_known_topics(self, mock_mqtt_client):
        client = PersistentBrokerClient("10.0.0.5", 1883)
        client.ensure_subscribed("topic/a")
        client.ensure_subscribed("topic/b")
        mock_mqtt_client.subscribe.reset_mock()

        client._on_connect(mock_mqtt_client, None, None, 0)

        assert mock_mqtt_client.subscribe.call_count == 2

    def test_wait_for_fresh_data_returns_empty_dict_when_nothing_arrives(self, mock_mqtt_client):
        client = PersistentBrokerClient("10.0.0.5", 1883)

        result = client.wait_for_fresh_data(max_wait=0.05, settle=0.01)

        assert result == {}

    def test_wait_for_fresh_data_returns_accumulated_state_once_a_message_arrives(self, mock_mqtt_client):
        client = PersistentBrokerClient("10.0.0.5", 1883)

        def deliver_message():
            message = MagicMock()
            message.topic = "openWB/internal_chargepoint/0/get/power"
            message.payload = b"1500"
            client._on_message(mock_mqtt_client, None, message)

        threading.Timer(0.02, deliver_message).start()

        result = client.wait_for_fresh_data(max_wait=1, settle=0.05)

        assert result == {"openWB/internal_chargepoint/0/get/power": 1500}

    def test_wait_for_fresh_data_keeps_previously_received_topics(self, mock_mqtt_client):
        """Ein Zyklus mit nur teilweise neuen Daten darf frueher empfangene Topics nicht verlieren -
        genau das war die Ursache des Bugs, den PR #3976 zu beheben versuchte."""
        client = PersistentBrokerClient("10.0.0.5", 1883)
        first_message = MagicMock()
        first_message.topic = "openWB/internal_chargepoint/0/get/power"
        first_message.payload = b"1500"
        client._on_message(mock_mqtt_client, None, first_message)

        def deliver_second_message():
            message = MagicMock()
            message.topic = "openWB/internal_chargepoint/0/get/currents"
            message.payload = b"[1.0, 1.0, 1.0]"
            client._on_message(mock_mqtt_client, None, message)

        threading.Timer(0.02, deliver_second_message).start()

        result = client.wait_for_fresh_data(max_wait=1, settle=0.05)

        assert result == {
            "openWB/internal_chargepoint/0/get/power": 1500,
            "openWB/internal_chargepoint/0/get/currents": [1.0, 1.0, 1.0],
        }

    def test_wait_for_fresh_data_registers_and_deregisters_its_own_waiter(self, mock_mqtt_client):
        client = PersistentBrokerClient("10.0.0.5", 1883)

        client.wait_for_fresh_data(max_wait=0.02, settle=0.01)

        assert client._waiters == []

    def test_on_message_notifies_all_concurrent_waiters(self, mock_mqtt_client):
        """Bei zwei Ladepunkten an einem Secondary (duo_num 0/1, gemeinsame Verbindung) laufen
        mehrere wait_for_fresh_data()-Aufrufe gleichzeitig auf demselben PersistentBrokerClient -
        eine eingehende Nachricht muss alle wecken, nicht nur den zuerst registrierten."""
        client = PersistentBrokerClient("10.0.0.5", 1883)
        waiter_a = threading.Event()
        waiter_b = threading.Event()
        client._waiters.extend([waiter_a, waiter_b])

        message = MagicMock()
        message.topic = "some/topic"
        message.payload = b"1"
        client._on_message(mock_mqtt_client, None, message)

        assert waiter_a.is_set()
        assert waiter_b.is_set()

    def test_wait_for_fresh_data_both_duo_waiters_receive_their_data(self, mock_mqtt_client):
        """Reproduziert das im Review zu PR #3996 beschriebene Szenario: zwei Ladepunkte am selben
        Secondary (duo_num 0/1) rufen wait_for_fresh_data() auf demselben PersistentBrokerClient
        nahezu gleichzeitig auf. Mit einem einzigen gemeinsamen Event konnte ein Aufrufer per eigenem
        clear() dem anderen den Wakeup wegnehmen (verpasste Daten trotz eingetroffener Nachricht) -
        mit einem Event je Aufrufer kann das nicht mehr passieren."""
        client = PersistentBrokerClient("10.0.0.5", 1883)
        results = {}

        def waiter(name):
            results[name] = client.wait_for_fresh_data(max_wait=1, settle=0.05)

        t1 = threading.Thread(target=waiter, args=("cp0",))
        t2 = threading.Thread(target=waiter, args=("cp1",))
        t1.start()
        t2.start()

        deadline = time.monotonic() + 1
        while len(client._waiters) < 2 and time.monotonic() < deadline:
            time.sleep(0.005)
        assert len(client._waiters) == 2

        for topic, payload in [
            ("openWB/internal_chargepoint/0/get/power", b"1500"),
            ("openWB/internal_chargepoint/1/get/power", b"2500"),
        ]:
            message = MagicMock()
            message.topic = topic
            message.payload = payload
            client._on_message(mock_mqtt_client, None, message)

        t1.join(timeout=2)
        t2.join(timeout=2)

        expected = {
            "openWB/internal_chargepoint/0/get/power": 1500,
            "openWB/internal_chargepoint/1/get/power": 2500,
        }
        assert results["cp0"] == expected
        assert results["cp1"] == expected


class TestGetPersistentBrokerClient:
    def test_returns_same_instance_for_same_host_and_port(self, mock_mqtt_client):
        broker._persistent_clients.clear()

        first = get_persistent_broker_client("10.0.0.5", 1883)
        second = get_persistent_broker_client("10.0.0.5", 1883)

        assert first is second

    def test_returns_different_instance_for_different_host(self, mock_mqtt_client):
        broker._persistent_clients.clear()

        first = get_persistent_broker_client("10.0.0.5", 1883)
        second = get_persistent_broker_client("10.0.0.6", 1883)

        assert first is not second
