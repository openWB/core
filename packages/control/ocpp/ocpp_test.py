import asyncio
import concurrent.futures
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock
import pytest

from control import data
from control.chargepoint.chargepoint import Chargepoint
from control.chargepoint.chargepoint_template import CpTemplate
from control.counter import Counter
from control.ev.ev import Ev
from control.ocpp import ocpp_connection_manager
from control.ocpp import ocpp_client
from control.ocpp import ocpp_transaction_coordinator
from control.ocpp.ocpp_chargepoint import OcppChargePoint
from control.ocpp.ocpp_client import OcppClient
from control.ocpp.ocpp_connection import OcppConnection, RegistrationState
from control.ocpp.ocpp_connection_manager import OcppConnectionManager
from control.ocpp.ocpp_transaction_coordinator import AuthorizationResult, TransactionCoordinator
from ocpp.v16.enums import (
    ChargePointStatus,
    MessageTrigger,
    RegistrationStatus,
    TriggerMessageStatus,
)
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


@pytest.mark.parametrize("result", [
    AuthorizationResult(status="Accepted"),
    AuthorizationResult(status="Blocked"),
    AuthorizationResult(error="offline"),
])
def test_client_authorize_returns_result_future(monkeypatch, result):
    client = object.__new__(OcppClient)
    client.loop = Mock()
    client.transactions = SimpleNamespace(authorize=AsyncMock(return_value=result))

    def submit(coroutine, loop):
        assert loop is client.loop
        future = concurrent.futures.Future()
        future.set_result(asyncio.run(coroutine))
        return future

    monkeypatch.setattr(ocpp_client.asyncio, "run_coroutine_threadsafe", submit)

    future = client.authorize("box-1", "TAG")

    assert isinstance(future, concurrent.futures.Future)
    assert future.result(timeout=1) is result
    client.transactions.authorize.assert_awaited_once_with(chargebox_id="box-1", id_tag="TAG")

    async def check():
        assert await asyncio.wrap_future(future) is result

    asyncio.run(check())


def test_client_authorize_future_can_be_cancelled(monkeypatch):
    client = object.__new__(OcppClient)
    client.loop = Mock()
    client.transactions = SimpleNamespace(authorize=AsyncMock())
    submitted = []

    def submit(coroutine, loop):
        submitted.append(coroutine)
        return concurrent.futures.Future()

    monkeypatch.setattr(ocpp_client.asyncio, "run_coroutine_threadsafe", submit)

    future = client.authorize("box-1", "TAG")
    try:
        assert future.cancel()
        with pytest.raises(concurrent.futures.CancelledError):
            future.result(timeout=1)
    finally:
        for coroutine in submitted:
            coroutine.close()


@pytest.mark.parametrize("authorize_stop", [False, True])
def test_client_request_stop_forwards_authorization(monkeypatch, authorize_stop):
    client = object.__new__(OcppClient)
    client.loop = Mock()
    client.transactions = SimpleNamespace(stop=AsyncMock(return_value=True))

    def submit(coroutine, loop):
        assert loop is client.loop
        future = concurrent.futures.Future()
        future.set_result(asyncio.run(coroutine))
        return future

    monkeypatch.setattr(ocpp_client.asyncio, "run_coroutine_threadsafe", submit)
    options = {"authorize_stop": True} if authorize_stop else {}

    assert client.request_stop("box-1", 150, "TAG", "Local", **options) is None

    client.transactions.stop.assert_awaited_once_with(
        chargebox_id="box-1", imported=150, id_tag="TAG", reason="Local", authorize_stop=authorize_stop,
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
        123456,
        9876,
    )
    snapshot = client._meter_snapshots["cp1"]
    assert snapshot.transaction_id == 123456
    assert snapshot.connector_id == 1
    assert snapshot.imported == 9876


@pytest.mark.parametrize(
    "previous, chargebox_id, active, expected_disconnects",
    [
        pytest.param(None, "box-1", False, ["box-1"], id="initial-disabled-config"),
        pytest.param(("box-1", True), "box-1", False, ["box-1"], id="disable-ocpp"),
        pytest.param(("box-1", True), "box-2", True, ["box-1"], id="change-id"),
        pytest.param(("box-1", False), "box-2", False, ["box-1", "box-2"],
                     id="change-id-while-disabled"),
    ],
)
def test_sync_chargepoint_lifecycle(
    previous, chargebox_id, active, expected_disconnects
):
    client = object.__new__(OcppClient)
    client._chargepoint_lifecycle = {}
    if previous is not None:
        client._chargepoint_lifecycle[1] = previous
    disconnect = Mock()
    client.disconnect = disconnect

    client.sync_chargepoint_lifecycle(1, chargebox_id, active)

    assert [call.args[0] for call in disconnect.call_args_list] == expected_disconnects
    assert client._chargepoint_lifecycle[1] == (chargebox_id, bool(active and chargebox_id))


def test_status_notification_skips_connection_check_when_status_is_unchanged():
    client = object.__new__(OcppClient)
    client._last_update = {
        ("cp1", 1): (ChargePointStatus.available, "NoError", ""),
    }
    client.connection_manager = SimpleNamespace(connect=AsyncMock())

    asyncio.run(client._send_status_notification(
        chargebox_id="cp1",
        connector_id=1,
        fault_state=0,
        fault_state_str="",
        status=ChargePointStatus.available,
        force=False,
    ))

    client.connection_manager.connect.assert_not_awaited()


def test_status_notification_updates_client_cache_after_successful_send():
    chargepoint = SimpleNamespace(_status_notification=AsyncMock(return_value=object()))
    client = object.__new__(OcppClient)
    client._last_update = {}
    client.connection_manager = SimpleNamespace(
        connect=AsyncMock(return_value=SimpleNamespace(
            cp=chargepoint,
            boot_accepted=True,
        )),
    )

    asyncio.run(client._send_status_notification(
        chargebox_id="cp1",
        connector_id=1,
        fault_state=0,
        fault_state_str="x" * 60,
        status=ChargePointStatus.available,
        force=False,
    ))

    client.connection_manager.connect.assert_awaited_once_with("cp1")
    chargepoint._status_notification.assert_awaited_once()
    assert chargepoint._status_notification.await_args.kwargs["fault_state_str"] == "x" * 50
    assert client._last_update[("cp1", 1)] == (
        ChargePointStatus.available,
        "NoError",
        "x" * 50,
    )


def test_trigger_message_decisions(monkeypatch):
    from control.ocpp import ocpp_chargepoint

    openwb_cp = SimpleNamespace(
        num=1,
        data=SimpleNamespace(get=SimpleNamespace(
            ocpp=SimpleNamespace(availability=True),
        )),
    )
    monkeypatch.setattr(ocpp_chargepoint, "get_cp_from_chargebox_id", lambda _: openwb_cp)

    async def check():
        cp = OcppChargePoint("box-1", Mock(), trigger_msg_callback=AsyncMock())
        assert (await cp.trigger_message(MessageTrigger.heartbeat,
                                         connector_id=99)).status == TriggerMessageStatus.accepted
        assert (await cp.trigger_message(MessageTrigger.status_notification)).status == TriggerMessageStatus.accepted
        assert (await cp.trigger_message(MessageTrigger.status_notification,
                                         connector_id=2)).status == TriggerMessageStatus.rejected
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
        client.connection_manager = SimpleNamespace(
            is_active_charge_point=Mock(return_value=True),
        )
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
        client.connection_manager = SimpleNamespace(
            is_active_charge_point=Mock(side_effect=[True, True, False]),
        )
        await client.handler_trigger_msg(cp, MessageTrigger.status_notification, 1)
        await client.handler_trigger_msg(cp, MessageTrigger.status_notification, 1)
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
        client.connection_manager = SimpleNamespace(
            is_active_charge_point=Mock(return_value=True),
        )
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


@pytest.mark.parametrize("has_snapshot", [True, False])
def test_trigger_meter_values_uses_snapshot_or_skips_when_missing(has_snapshot):
    chargepoint = SimpleNamespace(
        chargebox_id="box-1",
        _meter_values=AsyncMock(),
    )
    client = object.__new__(OcppClient)
    client.connection_manager = SimpleNamespace(
        is_active_charge_point=Mock(return_value=True),
    )
    client._meter_snapshots = (
        {"box-1": SimpleNamespace(connector_id=1, imported=9876)}
        if has_snapshot else {}
    )
    client.transactions = SimpleNamespace(
        get_transaction_id=Mock(return_value=42),
    )

    asyncio.run(client.handler_trigger_msg(
        chargepoint,
        MessageTrigger.meter_values,
        1,
    ))

    client.connection_manager.is_active_charge_point.assert_called_once_with(chargepoint)
    if has_snapshot:
        client.transactions.get_transaction_id.assert_called_once_with("box-1")
        chargepoint._meter_values.assert_awaited_once()
        kwargs = chargepoint._meter_values.await_args.kwargs
        assert kwargs["connector_id"] == 1
        assert kwargs["transaction_id"] == 42
        assert kwargs["meter_value"][0]["sampledValue"][0] == {
            "value": "9876",
            "context": "Trigger",
            "format": "Raw",
            "measurand": "Energy.Active.Import.Register",
            "unit": "Wh",
        }
    else:
        client.transactions.get_transaction_id.assert_called_once_with("box-1")
        chargepoint._meter_values.assert_not_awaited()


def test_trigger_diagnostics_status_sends_stored_status():
    chargepoint = SimpleNamespace(_diagnostics_status=AsyncMock())
    client = object.__new__(OcppClient)
    client.connection_manager = SimpleNamespace(
        is_active_charge_point=Mock(return_value=True),
    )

    asyncio.run(client.handler_trigger_msg(
        chargepoint,
        MessageTrigger.diagnostics_status_notification,
        None,
    ))

    chargepoint._diagnostics_status.assert_awaited_once_with(None)


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

    connection_manager = OcppConnectionManager(
        chargepoint_factory=Mock(),
        on_connected=AsyncMock(),
        on_disconnected=AsyncMock(),
    )

    connect_mock = Mock()
    monkeypatch.setattr(ocpp_connection_manager.websockets, "connect", connect_mock)

    result = asyncio.run(connection_manager.connect("invalid-cp"))

    assert result is None
    connect_mock.assert_not_called()
    assert connection_manager.is_wanted("invalid-cp") is False


def test_connection_transport_is_usable_before_registration_is_accepted():
    connection = OcppConnection(
        chargebox_id="box-1",
        ws=SimpleNamespace(closed=False),
        cp=Mock(),
    )
    connection.start_task = Mock(done=Mock(return_value=False))
    connection.registration_state = RegistrationState.PENDING

    assert connection.boot_accepted is False
    assert OcppConnectionManager._is_usable(connection) is True


def test_pending_boot_notification_keeps_connection_unaccepted():
    client = object.__new__(OcppClient)
    client.connection_manager = SimpleNamespace()
    connection = OcppConnection("box-1", SimpleNamespace(closed=False), SimpleNamespace())

    async def check():
        result = await client._handle_boot_response(
            connection,
            SimpleNamespace(status=RegistrationStatus.pending, interval=30),
        )
        assert result is True

    asyncio.run(check())

    assert connection.registration_state == RegistrationState.PENDING
    assert connection.cp.registration_state == RegistrationState.PENDING
    assert connection.boot_accepted is False
    assert connection.heartbeat_task is None
    assert connection.meter_task is None


def test_rejected_boot_notification_schedules_interval_retry():
    client = object.__new__(OcppClient)
    client.connection_manager = SimpleNamespace()
    connection = OcppConnection("box-1", SimpleNamespace(closed=False), SimpleNamespace())

    async def check():
        await client._handle_boot_response(
            connection,
            SimpleNamespace(status=RegistrationStatus.rejected, interval=17),
        )
        assert connection.registration_state == RegistrationState.REJECTED
        assert connection.retry_interval == 17
        assert connection.retry_task is not None
        connection.retry_task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await connection.retry_task

    asyncio.run(check())


def test_rejected_boot_notification_retries_on_same_connection_until_accepted(monkeypatch):
    client = object.__new__(OcppClient)
    client._start_accepted_connection = AsyncMock()
    delays = []

    async def immediate_sleep(delay):
        delays.append(delay)

    monkeypatch.setattr(asyncio, "sleep", immediate_sleep)
    chargepoint = SimpleNamespace(
        registration_state=None,
        _boot_notification=AsyncMock(side_effect=[
            SimpleNamespace(status=RegistrationStatus.rejected, interval=2),
            SimpleNamespace(status=RegistrationStatus.accepted, interval=30),
        ]),
    )
    connection = OcppConnection(
        "box-1",
        SimpleNamespace(closed=False),
        chargepoint,
    )
    connection.registration_state = RegistrationState.REJECTED
    connection.retry_interval = 0.01
    client.connection_manager = SimpleNamespace(get=Mock(return_value=connection))

    async def check():
        connection.retry_task = asyncio.create_task(
            client._retry_registration(connection),
        )
        await connection.retry_task

    asyncio.run(check())

    assert chargepoint._boot_notification.await_count == 2
    assert connection.registration_state == RegistrationState.ACCEPTED
    assert connection.boot_accepted is True
    assert delays == [0.01, 2]
    client._start_accepted_connection.assert_awaited_once()
    client.connection_manager.get.assert_called_with("box-1")


def test_rejected_charge_point_ignores_inbound_calls_but_receives_call_results():
    sent_messages = []

    async def send(message):
        sent_messages.append(json.loads(message))

    async def check():
        cp = OcppChargePoint("box-1", SimpleNamespace(send=send))
        cp.registration_state = RegistrationState.REJECTED
        await cp.route_message(json.dumps([
            2,
            "trigger-1",
            "TriggerMessage",
            {"requestedMessage": "Heartbeat"},
        ]))
        await cp.route_message(json.dumps([3, "boot-retry", {}]))

        assert sent_messages == []
        response = cp._response_queue.get_nowait()
        assert response.unique_id == "boot-retry"

    asyncio.run(check())


def test_pending_trigger_is_sent_after_confirmation(monkeypatch):
    from control.ocpp import ocpp_chargepoint

    events = []

    async def send(message):
        events.append(json.loads(message))

    openwb_cp = SimpleNamespace(num=1, data=SimpleNamespace(get=SimpleNamespace(
        ocpp=SimpleNamespace(availability=True),
    )))
    monkeypatch.setattr(ocpp_chargepoint, "get_cp_from_chargebox_id", lambda _: openwb_cp)
    client = object.__new__(OcppClient)
    connection = SimpleNamespace(registration_state=RegistrationState.PENDING)

    async def check():
        cp = OcppChargePoint(
            "box-1",
            SimpleNamespace(send=send),
            trigger_msg_callback=client.handler_trigger_msg,
        )
        connection.cp = cp
        cp._heartbeat = AsyncMock(side_effect=lambda: events.append("Heartbeat"))
        client.connection_manager = SimpleNamespace(
            is_active_charge_point=Mock(return_value=False),
            get=Mock(return_value=connection),
        )
        await cp.route_message(json.dumps([
            2,
            "trigger-pending",
            "TriggerMessage",
            {"requestedMessage": "Heartbeat"},
        ]))
        await asyncio.sleep(0)

    asyncio.run(check())

    assert events == [[3, "trigger-pending", {"status": "Accepted"}], "Heartbeat"]


@pytest.mark.parametrize(
    ("action", "payload"),
    [
        ("RemoteStartTransaction", {"idTag": "TAG", "connectorId": 1}),
        ("RemoteStopTransaction", {"transactionId": 42}),
    ],
)
def test_pending_rejects_remote_transaction_requests(action, payload, monkeypatch):
    from control.ocpp import ocpp_chargepoint

    events = []

    async def send(message):
        events.append(json.loads(message))

    openwb_cp = SimpleNamespace(
        num=1,
        data=SimpleNamespace(get=SimpleNamespace(ocpp=SimpleNamespace(
            availability=True,
            transaction_id=42,
            remote_stop=False,
        ))),
    )
    monkeypatch.setattr(ocpp_chargepoint, "get_cp_from_chargebox_id", lambda _: openwb_cp)

    async def check():
        cp = OcppChargePoint("box-1", SimpleNamespace(send=send))
        cp.registration_state = RegistrationState.PENDING
        await cp.route_message(json.dumps([2, "pending-request", action, payload]))

    asyncio.run(check())

    assert events == [[3, "pending-request", {"status": "Rejected"}]]
    assert openwb_cp.data.get.ocpp.remote_stop is False


def test_transaction_start_does_not_authorize_before_boot_accepted(monkeypatch):
    openwb_cp = SimpleNamespace(
        num=1,
        data=SimpleNamespace(get=SimpleNamespace(ocpp=SimpleNamespace(
            availability=True,
            transaction_id=None,
            transaction_id_tag=None,
        ))),
    )
    authorize = AsyncMock()
    connection = SimpleNamespace(
        boot_accepted=False,
        cp=SimpleNamespace(_authorize=authorize),
    )
    coordinator = TransactionCoordinator(
        ensure_connected=AsyncMock(return_value=connection),
    )
    monkeypatch.setattr(
        ocpp_transaction_coordinator,
        "get_cp_from_chargebox_id",
        lambda _: openwb_cp,
    )
    monkeypatch.setattr(
        ocpp_transaction_coordinator,
        "Pub",
        lambda: SimpleNamespace(pub=Mock()),
    )

    result = asyncio.run(coordinator.start("box-1", 1, "TAG", 0))

    assert result is False
    authorize.assert_not_awaited()


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
    assert openwb_cp.data.get.ocpp.transaction_id is None
    assert openwb_cp.data.get.ocpp.transaction_id_tag is None
    assert openwb_cp.data.get.ocpp.tag_accepted is False
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
