from types import SimpleNamespace
import json
from urllib.parse import parse_qs
from unittest.mock import Mock

import pytest
import requests_mock
from requests import HTTPError

from control import data
from modules.consumers.openwb.wallbox_socket import consumer as wallbox_socket_consumer
from modules.consumers.openwb.wallbox_socket.config import WallboxSocket, WallboxSocketConfiguration


@pytest.fixture
def pro_socket(monkeypatch):
    data.data_init(Mock())
    cp_config = SimpleNamespace(type="openwb_pro", configuration=SimpleNamespace(ip_address="192.168.1.40"))
    monkeypatch.setattr(data.data, "cp_data", {
        "cp4": SimpleNamespace(chargepoint_module=SimpleNamespace(config=cp_config))})
    consumer = wallbox_socket_consumer.create_consumer(
        WallboxSocket(id=1, configuration=WallboxSocketConfiguration(chargepoint_id=4)))
    return consumer, cp_config


def socket_status():
    return dict(date="2026:11:17-13:29:54", timestamp=1794918594,
                socket_available=True, socket_switch_on=False, socket_is_on=True,
                power=449.0, current=2, voltage=224.5, energy=9.0, frequency=50.018)


@pytest.mark.parametrize("actual, target", [(True, False), (False, True)])
def test_reads_measured_values_and_actual_state(pro_socket, actual, target):
    consumer, _ = pro_socket
    status = socket_status()
    status.update(socket_is_on=actual, socket_switch_on=target)
    with requests_mock.Mocker() as http:
        http.get("http://192.168.1.40/socket.php", json=status)
        state = consumer.module_updater()

    assert state.state is actual
    assert state.power == 449.0
    assert state.powers == [449.0, 0, 0]
    assert state.currents == [2, 0, 0]
    assert state.voltages == [224.5, 0, 0]
    assert state.imported == 9.0
    assert state.exported == 0


def test_switch_commands_and_changed_chargepoint_address(pro_socket):
    consumer, cp_config = pro_socket
    with requests_mock.Mocker() as http:
        http.post("http://192.168.1.40/socket.php", text="OK")
        http.post("http://192.168.1.41/socket.php", text="OK")
        consumer.module_switch_on()
        cp_config.configuration.ip_address = "192.168.1.41"
        consumer.module_switch_off()

    assert [(request.url, parse_qs(request.text)) for request in http.request_history] == [
        ("http://192.168.1.40/socket.php", {"socket_switch_on": ["1"]}),
        ("http://192.168.1.41/socket.php", {"socket_switch_on": ["0"]}),
    ]


def test_missing_socket_reports_error_and_recovers(pro_socket):
    consumer, _ = pro_socket
    status = socket_status()
    status["socket_available"] = False
    with requests_mock.Mocker() as http:
        http.get("http://192.168.1.40/socket.php", [
            {"json": status}, {"json": socket_status()}])
        with pytest.raises(ValueError, match="keine Steckdose verbaut"):
            consumer.module_updater()
        assert consumer.module_updater().power == 449.0


@pytest.mark.parametrize("method", ["module_updater", "module_switch_on", "module_switch_off"])
def test_http_errors_are_not_silenced(pro_socket, method):
    consumer, _ = pro_socket
    with requests_mock.Mocker() as http:
        http.register_uri(requests_mock.ANY, "http://192.168.1.40/socket.php", status_code=503)
        with pytest.raises(HTTPError):
            getattr(consumer, method)()


def test_requires_existing_chargepoint(pro_socket):
    consumer, _ = pro_socket
    consumer.config.configuration.chargepoint_id = 99

    with requests_mock.Mocker() as http:
        with pytest.raises(KeyError, match="Ladepunkt auswählen"):
            consumer.module_updater()
        assert http.request_history == []


def test_selects_interface_from_current_linked_chargepoint_type(pro_socket, monkeypatch):
    consumer, cp_config = pro_socket
    publisher = Mock()
    monkeypatch.setattr(wallbox_socket_consumer, "pub_single", publisher)

    def broker_factory(name, on_connect, on_message, **kwargs):
        assert kwargs == {"host": "192.168.1.50", "port": 1883}

        def receive(timeout):
            for key, value in {"power": 100, "state": False, "rfid": "123"}.items():
                on_message(None, None, SimpleNamespace(
                    topic=f"openWB/internal_socket/get/{key}", payload=json.dumps(value).encode()))
        return Mock(start_finite_loop=receive)

    broker = Mock(side_effect=broker_factory)
    monkeypatch.setattr(wallbox_socket_consumer, "BrokerClient", broker)

    with requests_mock.Mocker() as http:
        http.get("http://192.168.1.40/socket.php", json=socket_status())
        http.post("http://192.168.1.40/socket.php", text="OK")
        assert consumer.module_updater().power == 449.0
        consumer.module_switch_on()
        consumer.module_clear_rfid()
        publisher.assert_not_called()
        broker.assert_not_called()

        cp_config.type = "external_openwb"
        cp_config.configuration.ip_address = "192.168.1.50"
        state = consumer.module_updater()
        assert state.power == 100
        assert state.rfid == "123"
        consumer.module_switch_off()
        publisher.assert_called_once_with(
            "openWB/set/internal_socket/data/set_state", False, hostname="192.168.1.50")
        consumer.module_clear_rfid()
        publisher.assert_called_with(
            "openWB/set/internal_socket/data/last_tag", None, hostname="192.168.1.50")

        cp_config.type = "openwb_pro"
        cp_config.configuration.ip_address = "192.168.1.40"
        assert consumer.module_updater().power == 449.0
        consumer.module_switch_off()
        assert len(http.request_history) == 4
