import errno
import threading
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
    def test_publish_raises_when_not_connected(self, mock_mqtt_client):
        mock_mqtt_client.is_connected.return_value = False
        client = PersistentBrokerClient("10.0.0.5", 1883)

        with pytest.raises(ConnectionError) as excinfo:
            client.publish("some/topic", "1")

        mock_mqtt_client.publish.assert_not_called()
        # errno muss gesetzt sein, sonst faellt der bestehende OSError-Handler
        # (helpermodules/exceptions/os.py) auf die nichtssagende "Unbekannter Fehler"-Meldung zurueck,
        # statt die schon vorhandene, uebersetzte "Verbindung zum Host fehlgeschlagen"-Meldung zu nutzen.
        assert excinfo.value.errno == errno.EHOSTUNREACH
        assert handle_os_error(excinfo.value) == (
            "Die Verbindung zum Host ist fehlgeschlagen. Überprüfe Adresse und Netzwerk.")

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
