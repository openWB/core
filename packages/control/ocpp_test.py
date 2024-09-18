from unittest.mock import Mock
import pytest

from control import data
from control.chargepoint.chargepoint import Chargepoint
from modules.devices.mqtt.config import Mqtt
from modules.devices.mqtt.device import create_device


@pytest.fixture()
def mock_data() -> None:
    data.data_init(Mock())
    data.data.optional_data.data.ocpp.active = True
    data.data.optional_data.data.ocpp.url = "ws://localhost:9000/"


def test_start_transaction(mock_data, monkeypatch):
    cp = Chargepoint(1, None)
    cp.data.config.ocpp_chargebox_id = "cp1"
    cp.data.get.plug_state = True

    start_transaction_mock = Mock()
    monkeypatch.setattr(data.data.optional_data, "start_transaction", start_transaction_mock)
    _pub_configured_ev_mock = Mock()
    monkeypatch.setattr(cp, "_pub_configured_ev", _pub_configured_ev_mock)
    prepare_cp_mock = Mock(return_value=(-1, None))
    monkeypatch.setattr(cp, "prepare_cp", prepare_cp_mock)

    cp.update([])

    assert start_transaction_mock.call_args == (("cp1", 1, None, 0),)


def test_stop_transaction(mock_data, monkeypatch):
    cp = Chargepoint(1, None)
    cp.data.config.ocpp_chargebox_id = "cp1"
    cp.data.get.plug_state = False
    cp.data.set.ocpp_transaction_id = 124
    cp.data.set.charging_ev_prev = -1

    stop_transaction_mock = Mock()
    monkeypatch.setattr(data.data.optional_data, "stop_transaction", stop_transaction_mock)

    cp._process_charge_stop()

    assert stop_transaction_mock.call_args == (("cp1", 0, 124, None),)


def test_send_ocpp_data(mock_data, monkeypatch):
    data.data.cp_data["cp1"] = Chargepoint(1, None)
    data.data.cp_data["cp1"].data.config.ocpp_chargebox_id = "cp1"
    data.data.cp_data["cp1"].data.get.plug_state = True
    data.data.cp_data["cp1"].chargepoint_module = create_device(Mqtt())
    data.data.cp_data["cp1"].data.get.serial_number = "123456"
    transfer_values_mock = Mock()
    monkeypatch.setattr(data.data.optional_data, "transfer_values", transfer_values_mock)
    boot_notification_mock = Mock()
    monkeypatch.setattr(data.data.optional_data, "boot_notification", boot_notification_mock)
    send_heart_beat_mock = Mock()
    monkeypatch.setattr(data.data.optional_data, "send_heart_beat", send_heart_beat_mock)

    data.data.optional_data.ocpp_boot_notification_send = False

    data.data.optional_data._transfer_meter_values()

    boot_notification_mock.call_args == (("cp1", "mqtt", "123456"),)
    send_heart_beat_mock.call_args == (("cp1",),)
    transfer_values_mock.call_args == (("cp1", 1, 0),)
    assert data.data.optional_data.ocpp_boot_notification_send is True
