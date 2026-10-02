import asyncio
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, PropertyMock
import pytest

from control import data
from control.chargepoint.chargepoint import Chargepoint
from control.chargepoint.chargepoint_template import CpTemplate
from control.counter import Counter
from control.ev.ev import Ev
from control.ocpp import ocpp_client
from control.ocpp import ocpp_transaction_coordinator
from control.ocpp.ocpp_chargepoint import OcppChargePoint
from control.ocpp.ocpp_client import OcppClient
from control.ocpp.ocpp_transaction_coordinator import TransactionCoordinator
from ocpp.v16.enums import ChargePointStatus, MessageTrigger, TriggerMessageStatus
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
    cp.data.get.ocpp.connected = True
    cp.template = CpTemplate()
    cp.chargepoint_module = ChargepointModule(Mqtt())

    request_start_mock = Mock()
    monkeypatch.setattr(data.data.ocpp_client, "request_start", request_start_mock)
    monkeypatch.setattr(cp, "_process_charge_stop", Mock())
    _pub_configured_ev_mock = Mock()
    monkeypatch.setattr(cp, "_pub_configured_ev", _pub_configured_ev_mock)

    cp.update({"ev0": Ev(0)})

    request_start_mock.assert_called_once_with(
        chargebox_id="cp1",
        connector_id=1,
        id_tag="ABCDEF01234567",
        imported=0,
    )


def test_stop_transaction(mock_data, monkeypatch):
    cp = Chargepoint(1, None)
    cp.data.config.ocpp_chargebox_id = "cp1"
    cp.data.set.rfid = "ABCDEF01234567"
    cp.data.config.ev = 1
    cp.data.get.plug_state = False
    cp.data.get.ocpp.transaction_id = 124
    cp.chargepoint_module = ChargepointModule(Mqtt())
    cp.template = CpTemplate()

    request_stop_mock = Mock()
    monkeypatch.setattr(data.data.ocpp_client, "request_stop", request_stop_mock)

    get_evu_counter_mock = Mock(return_value=Mock(spec=Counter))
    monkeypatch.setattr(data.data.counter_all_data, "get_evu_counter", get_evu_counter_mock)
    data.data.ev_data["ev1"] = Ev(1)

    cp._process_charge_stop()

    # assert request_stop_mock.call_args == (("cp1", cp.chargepoint_module.fault_state, 0, 124, None),)
    request_stop_mock.assert_called_once_with(
        chargebox_id="cp1",
        id_tag="ABCDEF01234567",
        imported=0,
        reason="EVDisconnected"
    )


def test_transfer_values_updates_meter_snapshot():
    client = object.__new__(OcppClient)
    client._meter_snapshots = {}
    loop = Mock()
    loop.call_soon_threadsafe.side_effect = lambda callback, *args: callback(*args)
    client.loop = loop

    client.transfer_values("cp1", 1, 123456, 9876)

    loop.call_soon_threadsafe.assert_called_once_with(
        client._set_meter_snapshot,
        "cp1",
        1,
        9876,
    )
    snapshot = client._meter_snapshots["cp1"]
    assert snapshot.connector_id == 1
    assert snapshot.imported == 9876


def test_trigger_message_decisions(monkeypatch):
    from control.ocpp import ocpp_chargepoint

    openwb_cp = SimpleNamespace(
        num=1,
        data=SimpleNamespace(get=SimpleNamespace(
            ocpp=SimpleNamespace(availability=True),
        )),
    )
    monkeypatch.setattr(ocpp_chargepoint, "get_cp_from_chargebox_id", lambda _: openwb_cp)
    cp = OcppChargePoint("box-1", Mock(), trigger_msg_callback=AsyncMock())

    async def check():
        assert (await cp.trigger_message(MessageTrigger.heartbeat, connector_id=99)).status == TriggerMessageStatus.accepted
        assert (await cp.trigger_message(MessageTrigger.status_notification)).status == TriggerMessageStatus.accepted
        assert (await cp.trigger_message(MessageTrigger.status_notification, connector_id=2)).status == TriggerMessageStatus.rejected
        assert (await cp.trigger_message(MessageTrigger.boot_notification)).status == TriggerMessageStatus.accepted

    asyncio.run(check())


@pytest.mark.parametrize("connector_id", [None, 0, 1])
def test_trigger_status_message_after_confirmation(monkeypatch, connector_id):
    from control.ocpp import ocpp_chargepoint

    events = []

    async def send(message):
        events.append(json.loads(message))

    async def call(payload):
        events.append(payload)

    openwb_cp = SimpleNamespace(
        num=1,
        data=SimpleNamespace(get=SimpleNamespace(
            ocpp=SimpleNamespace(availability=True), fault_state=1, fault_str="error",
        )),
        get_ocpp_status=Mock(return_value=ChargePointStatus.charging),
    )
    monkeypatch.setattr(ocpp_chargepoint, "get_cp_from_chargebox_id", lambda _: openwb_cp)
    ws = SimpleNamespace(send=send, closed=False)
    client = object.__new__(OcppClient)

    request = {"requestedMessage": "StatusNotification"}
    if connector_id is not None:
        request["connectorId"] = connector_id

    async def check():
        cp = OcppChargePoint("box-1", ws, trigger_msg_callback=client.handler_trigger_msg)
        cp.call = call
        client.connections = {"box-1": SimpleNamespace(cp=cp, ws=ws, closing=False, boot_accepted=True)}
        await cp.route_message(json.dumps([2, "trigger-1", "TriggerMessage", request]))
        await asyncio.sleep(0)

    asyncio.run(check())

    assert events[0] == [3, "trigger-1", {"status": "Accepted"}]
    notifications = events[1:]
    assert len(notifications) == 1
    assert notifications[0].connector_id == 1
    assert notifications[0].status == ChargePointStatus.charging
    assert notifications[0].info == "error"
    openwb_cp.get_ocpp_status.assert_called_once_with()


def test_trigger_status_forces_repeat_and_skips_old_connection(monkeypatch):
    from control.ocpp import ocpp_chargepoint

    openwb_cp = SimpleNamespace(
        num=1,
        data=SimpleNamespace(get=SimpleNamespace(
            ocpp=SimpleNamespace(availability=True), fault_state=0, fault_str="",
        )),
        get_ocpp_status=Mock(return_value=ChargePointStatus.available),
    )
    monkeypatch.setattr(ocpp_chargepoint, "get_cp_from_chargebox_id", lambda _: openwb_cp)
    ws = SimpleNamespace(closed=False)
    client = object.__new__(OcppClient)
    calls = []

    async def record(payload):
        calls.append(payload)

    async def check():
        cp = OcppChargePoint("box-1", ws, trigger_msg_callback=client.handler_trigger_msg)
        cp.call = record
        client.connections = {"box-1": SimpleNamespace(cp=cp, ws=ws, closing=False, boot_accepted=True)}
        await client.handler_trigger_msg(cp, MessageTrigger.status_notification, 1)
        await client.handler_trigger_msg(cp, MessageTrigger.status_notification, 1)
        client.connections["box-1"].cp = Mock()
        await client.handler_trigger_msg(cp, MessageTrigger.status_notification, 1)

    asyncio.run(check())

    assert len(calls) == 2
    assert all(payload.connector_id == 1 for payload in calls)


def test_trigger_heartbeat_ignores_connector_and_rejects_unsupported(monkeypatch):
    from control.ocpp import ocpp_chargepoint

    openwb_cp = SimpleNamespace(
        num=1,
        data=SimpleNamespace(get=SimpleNamespace(
            ocpp=SimpleNamespace(availability=True),
        )),
    )
    monkeypatch.setattr(ocpp_chargepoint, "get_cp_from_chargebox_id", lambda _: openwb_cp)
    events = []

    async def send(message):
        events.append(json.loads(message))

    ws = SimpleNamespace(send=send, closed=False)
    client = object.__new__(OcppClient)

    async def check():
        cp = OcppChargePoint("box-1", ws, trigger_msg_callback=client.handler_trigger_msg)

        async def heartbeat():
            events.append("Heartbeat")
        cp._heartbeat = heartbeat
        client.connections = {"box-1": SimpleNamespace(cp=cp, ws=ws, closing=False, boot_accepted=True)}
        await cp.route_message(json.dumps([2, "heartbeat", "TriggerMessage", {
            "requestedMessage": "Heartbeat", "connectorId": 99,
        }]))
        await asyncio.sleep(0)
        await cp.route_message(json.dumps([2, "rejected", "TriggerMessage", {
            "requestedMessage": "StatusNotification", "connectorId": 2,
        }]))
        await cp.route_message(json.dumps([2, "bootnotification", "TriggerMessage", {
            "requestedMessage": "BootNotification",
        }]))
        await asyncio.sleep(0)

    asyncio.run(check())

    assert events == [
        [3, "heartbeat", {"status": "Accepted"}],
        "Heartbeat",
        [3, "rejected", {"status": "Rejected"}],
        [3, "bootnotification", {"status": "Accepted"}],
    ]


def test_trigger_message_rejected_without_backend_or_callback(monkeypatch):
    from control.ocpp import ocpp_chargepoint

    monkeypatch.setattr(ocpp_chargepoint, "get_cp_from_chargebox_id", lambda _: None)

    async def check():
        cp = OcppChargePoint("box-1", Mock(), trigger_msg_callback=AsyncMock())
        assert (await cp.trigger_message(MessageTrigger.heartbeat)).status == TriggerMessageStatus.rejected
        monkeypatch.setattr(ocpp_chargepoint, "get_cp_from_chargebox_id", lambda _: SimpleNamespace(num=1))
        cp.trigger_msg_callback = None
        assert (await cp.trigger_message(MessageTrigger.status_notification)).status == TriggerMessageStatus.rejected

    asyncio.run(check())


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
                    tag_accepted=False,
                )
            )
        ),
    )
    pub = Mock()
    coordinator = TransactionCoordinator(ensure_connected=AsyncMock(return_value=None))

    monkeypatch.setattr(ocpp_transaction_coordinator, "get_cp_from_chargebox_id", lambda _: openwb_cp)
    monkeypatch.setattr(ocpp_transaction_coordinator, "Pub", lambda: SimpleNamespace(pub=pub))

    asyncio.run(coordinator.stop("box-1", 1234, "", "EVDisconnected"))

    # nach dem die Transaktion gepseichert wurde, wird die:
    # pending_transaktion gespeichert
    # und anschließend transaction_id und transaction_id_tag auf None und
    # tag_accepted auf False gesetzt
    assert openwb_cp.data.get.ocpp.transaction_id == None
    assert openwb_cp.data.get.ocpp.transaction_id_tag == None
    assert openwb_cp.data.get.ocpp.tag_accepted == False
    assert openwb_cp.data.get.ocpp.pending_transactions == [{
        "action": "stop",
        "transaction_id": 42,
        "id_tag": "TAG",
        "imported": 1234,
        "reason": "EVDisconnected",
    }]


def test_persisted_stop_is_sent_once(monkeypatch):
    openwb_cp = SimpleNamespace(
        num=1,
        data=SimpleNamespace(get=SimpleNamespace(ocpp=SimpleNamespace(
            transaction_id=None,
            transaction_id_tag=None,
            tag_accepted=False,
            pending_availability=False,
            pending_transactions=[{
                "action": "stop",
                "transaction_id": 42,
                "id_tag": "TAG",
                "imported": 1234,
                "reason": "EVDisconnected",
            }],
        ))),
    )
    stop_transaction = AsyncMock()
    cp = SimpleNamespace(
        openwb_num=1,
        openwb_cp=openwb_cp,
        transaction_id=None,
        _pending_availability={},
        _stop_transaction=stop_transaction,
        apply_pending_availability=AsyncMock(),
    )
    connection = SimpleNamespace(cp=cp)
    coordinator = TransactionCoordinator(ensure_connected=AsyncMock())
    pub = Mock()

    monkeypatch.setattr(ocpp_transaction_coordinator, "get_cp_from_chargebox_id", lambda _: openwb_cp)
    monkeypatch.setattr(ocpp_transaction_coordinator, "Pub", lambda: SimpleNamespace(pub=pub))

    async def replay_twice():
        await coordinator.on_connected("box-1", connection)
        await coordinator.on_connected("box-1", connection)

    asyncio.run(replay_twice())

    stop_transaction.assert_awaited_once_with(
        meter_stop=1234,
        transaction_id=42,
        reason="EVDisconnected",
        id_tag="TAG",
    )
    assert openwb_cp.data.get.ocpp.pending_transactions == []
    assert cp.transaction_id is None
    assert openwb_cp.data.get.ocpp.transaction_id is None
    assert pub.call_args_list[-1].args == (
        "openWB/set/chargepoint/1/get/ocpp/pending_transactions",
        [],
    )
