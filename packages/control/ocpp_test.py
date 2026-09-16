import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock
import pytest

from control import data
from control.chargepoint.chargepoint import Chargepoint
from control.chargepoint.chargepoint_template import CpTemplate
from control.counter import Counter
from control.ev.ev import Ev
from control.ocpp import ocpp_client
from control.ocpp.ocpp_chargepoint import OcppChargePoint
from control.ocpp.ocpp_client import OcppClient, OcppTransaction, PendingStop, TransactionState
from modules.chargepoints.mqtt.chargepoint_module import ChargepointModule
from modules.chargepoints.mqtt.config import Mqtt


@pytest.fixture()
def mock_data() -> None:
    data.data_init(Mock())
    data.data.optional_data.data.ocpp.config.active = True
    data.data.optional_data.data.ocpp.config.url = "ws://localhost:9000/"


def test_start_transaction(mock_data, monkeypatch):
    cp = Chargepoint(1, None)
    cp.data.config.ev = 0
    cp.data.config.ocpp_chargebox_id = "cp1"
    cp.data.set.rfid = "ABCDEF01234567"
    cp.data.get.plug_state = True
    cp.template = CpTemplate()
    cp.chargepoint_module = ChargepointModule(Mqtt())

    start_transaction_mock = Mock()
    monkeypatch.setattr(data.data.optional_data, "start_transaction", start_transaction_mock)
    _pub_configured_ev_mock = Mock()
    monkeypatch.setattr(cp, "_pub_configured_ev", _pub_configured_ev_mock)

    cp.update({"ev0": Ev(0)})

    assert start_transaction_mock.call_args == (("cp1", cp.chargepoint_module.fault_state, 1, "ABCDEF01234567", 0),)


def test_stop_transaction(mock_data, monkeypatch):
    cp = Chargepoint(1, None)
    cp.data.config.ocpp_chargebox_id = "cp1"
    cp.data.config.ev = 1
    cp.data.get.plug_state = False
    cp.data.set.ocpp_transaction_id = 124
    cp.chargepoint_module = ChargepointModule(Mqtt())
    cp.template = CpTemplate()

    stop_transaction_mock = Mock()
    monkeypatch.setattr(data.data.optional_data, "stop_transaction", stop_transaction_mock)
    get_evu_counter_mock = Mock(return_value=Mock(spec=Counter))
    monkeypatch.setattr(data.data.counter_all_data, "get_evu_counter", get_evu_counter_mock)
    data.data.ev_data["ev1"] = Ev(1)

    cp._process_charge_stop()

    assert stop_transaction_mock.call_args == (("cp1", cp.chargepoint_module.fault_state, 0, 124, None),)


def test_send_ocpp_data(mock_data, monkeypatch):
    data.data.cp_data["cp1"] = Chargepoint(1, None)
    data.data.cp_data["cp1"].data.config.ocpp_chargebox_id = "cp1"
    data.data.cp_data["cp1"].data.get.plug_state = True
    data.data.cp_data["cp1"].chargepoint_module = ChargepointModule(Mqtt())
    data.data.cp_data["cp1"].data.get.serial_number = "123456"
    transfer_values_mock = Mock()
    monkeypatch.setattr(data.data.optional_data, "transfer_values", transfer_values_mock)
    boot_notification_mock = Mock()
    monkeypatch.setattr(data.data.optional_data, "boot_notification", boot_notification_mock)
    send_heart_beat_mock = Mock()
    monkeypatch.setattr(data.data.optional_data, "send_heart_beat", send_heart_beat_mock)

    data.data.optional_data.data.ocpp.boot_notification_sent = False

    data.data.optional_data._transfer_meter_values()

    boot_notification_mock.call_args == (("cp1", "mqtt", "123456"),)
    send_heart_beat_mock.call_args == (("cp1",),)
    transfer_values_mock.call_args == (("cp1", 1, 0),)
    assert data.data.optional_data.data.ocpp.boot_notification_sent is True


def test_boot_notification_without_openwb_chargepoint(monkeypatch):
    monkeypatch.setattr(ocpp_client, "get_cp_from_chargebox_id", lambda _: None)
    cp = object.__new__(OcppChargePoint)
    cp.chargebox_id = "box-1"
    cp.openwb_cp = None
    cp.openwb_num = None
    cp.call = AsyncMock(return_value=SimpleNamespace(status="Accepted"))

    response = asyncio.run(cp._boot_notification())

    assert response.status == "Accepted"
    assert cp.call.await_count == 1


def test_invalid_chargebox_id_does_not_connect(monkeypatch):
    data.data_init(Mock())
    data.data.cp_data = {}

    client = object.__new__(OcppClient)
    client.connections = {}
    client._connect_locks = {}
    client._wanted_connections = {"invalid-cp"}

    connect_mock = Mock()
    monkeypatch.setattr(ocpp_client.websockets, "connect", connect_mock)

    result = asyncio.run(client._ensure_connected("invalid-cp"))

    assert result is None
    connect_mock.assert_not_called()
    assert "invalid-cp" not in client._wanted_connections


def test_offline_stop_is_persisted(monkeypatch):
    openwb_cp = SimpleNamespace(
        num=1,
        data=SimpleNamespace(
            get=SimpleNamespace(
                ocpp=SimpleNamespace(
                    transaction_id=42,
                    transaction_id_tag="TAG",
                    pending_transactions=[],
                )
            )
        ),
    )
    pub = Mock()
    client = object.__new__(OcppClient)
    client._transactions = {}
    client.connections = {}

    monkeypatch.setattr(ocpp_client, "get_cp_from_chargebox_id", lambda _: openwb_cp)
    monkeypatch.setattr(ocpp_client, "Pub", lambda: SimpleNamespace(pub=pub))

    asyncio.run(client._request_stop("box-1", 1234, "", "EVDisconnected"))

    assert openwb_cp.data.get.ocpp.transaction_id == 42
    assert openwb_cp.data.get.ocpp.transaction_id_tag == "TAG"
    assert openwb_cp.data.get.ocpp.pending_transactions == [{
        "action": "stop",
        "transaction_id": 42,
        "id_tag": "TAG",
        "imported": 1234,
        "reason": "EVDisconnected",
    }]
    assert pub.call_count == 1


def test_persisted_stop_is_sent_once(monkeypatch):
    openwb_cp = SimpleNamespace(
        num=1,
        data=SimpleNamespace(get=SimpleNamespace(ocpp=SimpleNamespace())),
    )
    stop_transaction = AsyncMock(side_effect=RuntimeError("response lost"))
    meter_values = AsyncMock(side_effect=RuntimeError("meter values failed"))
    connection = SimpleNamespace(
        cp=SimpleNamespace(
            openwb_num=1,
            _meter_values=meter_values,
            _stop_transaction=stop_transaction,
        ),
    )
    client = object.__new__(OcppClient)
    client._transactions = {
        "box-1": OcppTransaction(
            state=TransactionState.ACTIVE,
            transaction_id=42,
            id_tag="TAG",
            pending_stop=PendingStop(1234, "TAG", "EVDisconnected"),
        )
    }

    monkeypatch.setattr(ocpp_client, "get_cp_from_chargebox_id", lambda _: openwb_cp)
    monkeypatch.setattr(ocpp_client, "Pub", lambda: SimpleNamespace(pub=Mock()))

    asyncio.run(client._send_pending_stop("box-1", connection))
    asyncio.run(client._send_pending_stop("box-1", connection))

    assert stop_transaction.await_count == 1
    assert meter_values.await_args.kwargs == {
        "connector_id": 1,
        "transaction_id": 42,
        "meter_value": [
            {
                "timestamp": meter_values.await_args.kwargs["meter_value"][0]["timestamp"],
                "sampledValue": [
                    {
                        "value": "1234",
                        "context": "Transaction.End",
                        "format": "Raw",
                        "measurand": "Energy.Active.Import.Register",
                        "unit": "Wh",
                    }
                ],
            }
        ],
    }
    assert not hasattr(openwb_cp.data.get.ocpp, "transaction_id") or openwb_cp.data.get.ocpp.transaction_id is None
    assert not hasattr(openwb_cp.data.get.ocpp,
                       "transaction_id_tag") or openwb_cp.data.get.ocpp.transaction_id_tag is None
    assert not hasattr(openwb_cp.data.get.ocpp, "pending_stop") or openwb_cp.data.get.ocpp.pending_stop is None


def test_offline_start_is_queued(monkeypatch):
    openwb_cp = SimpleNamespace(
        num=1,
        data=SimpleNamespace(get=SimpleNamespace(ocpp=SimpleNamespace(pending_transactions=[]))),
    )
    pub = Mock()
    client = object.__new__(OcppClient)

    monkeypatch.setattr(ocpp_client, "get_cp_from_chargebox_id", lambda _: openwb_cp)
    monkeypatch.setattr(ocpp_client, "Pub", lambda: SimpleNamespace(pub=pub))

    client._persist_offline_transaction_event(
        "box-1",
        {
            "action": "start",
            "connector_id": 1,
            "id_tag": "TAG",
            "imported": 100,
        },
    )

    assert openwb_cp.data.get.ocpp.pending_transactions == [{
        "action": "start",
        "connector_id": 1,
        "id_tag": "TAG",
        "imported": 100,
    }]
    assert pub.call_count == 1
