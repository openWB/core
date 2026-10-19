import asyncio
import concurrent.futures
import io
import json
import logging
import threading
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, call
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
from helpermodules.logger import FORMAT_STR_DETAILED, FORMAT_STR_OCPP
from helpermodules.logging_context import OcppContextFilter, ocpp_logging_context


def test_ocpp_logging_context_is_task_local(monkeypatch):
    client = object.__new__(OcppClient)
    client.loop = asyncio.new_event_loop()
    output = io.StringIO()
    handler = logging.StreamHandler(output)
    handler.setFormatter(logging.Formatter(FORMAT_STR_OCPP))
    handler.addFilter(OcppContextFilter())
    loggers = [logging.getLogger("control.ocpp"), logging.getLogger("ocpp")]
    for logger in loggers:
        monkeypatch.setattr(logger, "level", logging.INFO)
        logger.addHandler(handler)
    thread = threading.Thread(target=client.loop.run_forever, name="OCPP-EventLoop", daemon=True)
    thread.start()
    ready = []

    async def worker(number):
        loggers[0].info("before %s", number)
        ready.append(number)
        while len(ready) < 2:
            await asyncio.sleep(0)
        loggers[1].info("after %s", number)

        async def child():
            loggers[1].info("child %s", number)

        await asyncio.create_task(child())

    try:
        futures = [client._submit(worker(number), "logging probe", f"box-{number}") for number in (3, 5)]
        for future in futures:
            future.result(timeout=5)
        for number in (3, 5):
            for message in ("before", "after", "child"):
                assert f"{{INFO:box-{number}}} - {message} {number}" in output.getvalue()
        loggers[0].info("global")
        assert "{INFO:MainThread} - global" in output.getvalue()
        record = logging.LogRecord("ocpp", logging.INFO, __file__, 1, "main", (), None)
        with ocpp_logging_context("box-3"):
            handler.filter(record)
        assert "{INFO:MainThread}" in logging.Formatter(FORMAT_STR_DETAILED).format(record)
    finally:
        client.loop.call_soon_threadsafe(client.loop.stop)
        thread.join(timeout=5)
        client.loop.close()
        for logger in loggers:
            logger.removeHandler(handler)
        handler.close()


@pytest.mark.parametrize("exception", [ValueError, asyncio.CancelledError])
def test_ocpp_logging_context_resets_after_exception(exception):
    context_filter = OcppContextFilter()
    with ocpp_logging_context("box-0"):
        with pytest.raises(exception):
            with ocpp_logging_context("box-5"):
                raise exception()
        record = logging.LogRecord("ocpp", logging.INFO, __file__, 1, "probe", (), None)
        context_filter.filter(record)
        assert record.ocpp_context == "box-0"
    context_filter.filter(record)
    assert record.ocpp_context == record.threadName


def test_ocpp_submit_error_uses_chargebox_context(monkeypatch):
    client = object.__new__(OcppClient)
    client.loop = Mock()
    future = concurrent.futures.Future()
    future.set_exception(ValueError("probe"))

    def submit(coroutine, loop):
        coroutine.close()
        return future

    monkeypatch.setattr(ocpp_client.asyncio, "run_coroutine_threadsafe", submit)
    records = []

    def capture_error(*args):
        record = logging.LogRecord("control.ocpp", logging.ERROR, __file__, 1, "probe", (), None)
        OcppContextFilter().filter(record)
        records.append(record)

    monkeypatch.setattr(ocpp_client.log, "exception", capture_error)

    async def job():
        pass

    assert client._submit(job(), "error probe", "old-box") is future
    assert records[0].ocpp_context == "old-box"
    OcppContextFilter().filter(records[0])
    assert records[0].ocpp_context == records[0].threadName


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


def test_authorize_for_rfid_publishes_result_and_deduplicates(monkeypatch, mock_pub):
    client = object.__new__(OcppClient)
    client._rfid_authorize_pending = set()
    authorization_future = concurrent.futures.Future()
    client.authorize = Mock(return_value=authorization_future)
    openwb_cp = SimpleNamespace(
        num=1,
        data=SimpleNamespace(get=SimpleNamespace(
            rfid="TAG",
            ocpp=SimpleNamespace(authorization_flow_status=None),
        )),
    )
    monkeypatch.setattr(ocpp_client, "get_cp_from_chargebox_id", lambda _: openwb_cp)

    future = client.authorize_for_rfid("box-1", "TAG")

    assert future is authorization_future
    assert client.authorize_for_rfid("box-1", "TAG") is None
    client.authorize.assert_called_once_with("box-1", "TAG")
    authorization_future.set_result(AuthorizationResult(status="Accepted"))

    assert client._rfid_authorize_pending == set()
    assert mock_pub.pub.call_args_list == [
        call("openWB/set/chargepoint/1/get/ocpp/authorization_flow_status", "init"),
        call("openWB/set/chargepoint/1/get/ocpp/authorization_flow_status", "accepted"),
    ]


def test_authorize_for_rfid_publishes_rejected_when_authorize_raises(monkeypatch, mock_pub):
    client = object.__new__(OcppClient)
    client._rfid_authorize_pending = set()
    client.authorize = Mock(side_effect=RuntimeError("offline"))
    openwb_cp = SimpleNamespace(
        num=1,
        data=SimpleNamespace(get=SimpleNamespace(
            rfid="TAG",
            ocpp=SimpleNamespace(authorization_flow_status=None),
        )),
    )
    monkeypatch.setattr(ocpp_client, "get_cp_from_chargebox_id", lambda _: openwb_cp)

    assert client.authorize_for_rfid("box-1", "TAG") is None

    assert client._rfid_authorize_pending == set()
    assert openwb_cp.data.get.ocpp.authorization_flow_status == "rejected"
    assert mock_pub.pub.call_args_list == [
        call("openWB/set/chargepoint/1/get/ocpp/authorization_flow_status", "init"),
        call("openWB/set/chargepoint/1/get/ocpp/authorization_flow_status", "rejected"),
    ]


def test_authorize_for_rfid_ignores_result_after_rfid_changes(monkeypatch, mock_pub):
    client = object.__new__(OcppClient)
    client._rfid_authorize_pending = set()
    authorization_future = concurrent.futures.Future()
    client.authorize = Mock(return_value=authorization_future)
    openwb_cp = SimpleNamespace(
        num=1,
        data=SimpleNamespace(get=SimpleNamespace(
            rfid="TAG",
            ocpp=SimpleNamespace(authorization_flow_status=None),
        )),
    )
    monkeypatch.setattr(ocpp_client, "get_cp_from_chargebox_id", lambda _: openwb_cp)

    client.authorize_for_rfid("box-1", "TAG")
    openwb_cp.data.get.rfid = "NEW-TAG"
    authorization_future.set_result(AuthorizationResult(status="Accepted"))

    assert client._rfid_authorize_pending == set()
    assert openwb_cp.data.get.ocpp.authorization_flow_status is None
    assert mock_pub.pub.call_args_list == [
        call("openWB/set/chargepoint/1/get/ocpp/authorization_flow_status", "init"),
        call("openWB/set/chargepoint/1/get/ocpp/authorization_flow_status", None),
    ]


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

    future = client.request_stop("box-1", 150, "TAG", "Local", **options)
    assert isinstance(future, concurrent.futures.Future)
    assert future.result(timeout=1) is True

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
    "previous, chargebox_id, chargebox_pw, active, expected_disconnects",
    [
        pytest.param(None, "box-1", "pw-1", False, ["box-1"], id="initial-disabled-config"),
        pytest.param(("box-1", "pw-1", True), "box-1", "pw-1", False, ["box-1"], id="disable-ocpp"),
        pytest.param(("box-1", "pw-1", True), "box-2", "pw-1", True, ["box-1"], id="change-id"),
        pytest.param(("box-1", "pw-1", False), "box-2", "pw-1", False, ["box-1", "box-2"],
                     id="change-id-while-disabled"),
        pytest.param(("box-1", "pw-1", True), "box-1", "pw-2", True, ["box-1"],
                     id="change-password"),
        pytest.param(("box-1", "pw-1", True), "box-1", "pw-1", True, [],
                     id="unchanged-password"),
    ],
)
def test_sync_chargepoint_lifecycle(
    previous, chargebox_id, chargebox_pw, active, expected_disconnects
):
    client = object.__new__(OcppClient)
    client._chargepoint_lifecycle = {}
    if previous is not None:
        client._chargepoint_lifecycle[1] = previous
    disconnect = Mock()
    client.disconnect = disconnect

    client.sync_chargepoint_lifecycle(1, chargebox_id, chargebox_pw, active)

    assert [call.args[0] for call in disconnect.call_args_list] == expected_disconnects
    assert client._chargepoint_lifecycle[1] == (
        chargebox_id, chargebox_pw, bool(active and chargebox_id)
    )


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
    connection = SimpleNamespace(
        cp=chargepoint,
        boot_accepted=True,
    )
    client.connection_manager = SimpleNamespace(
        connect=AsyncMock(),
    )

    asyncio.run(client._send_status_notification(
        chargebox_id="cp1",
        connector_id=1,
        fault_state=0,
        fault_state_str="x" * 60,
        status=ChargePointStatus.available,
        force=False,
        connection=connection,
    ))

    client.connection_manager.connect.assert_not_awaited()
    chargepoint._status_notification.assert_awaited_once()
    assert chargepoint._status_notification.await_args.kwargs["fault_state_str"] == "x" * 50
    assert client._last_update[("cp1", 1)] == (
        ChargePointStatus.available,
        "NoError",
        "x" * 50,
    )


@pytest.mark.parametrize("availability,controller_status", [
    ([True, True], ChargePointStatus.available),
    ([True, False], ChargePointStatus.available),
    ([False, True], ChargePointStatus.unavailable),
    ([False, False], ChargePointStatus.unavailable),
])
def test_initial_status_notifications_reuse_existing_connection(availability, controller_status):
    client = object.__new__(OcppClient)
    client._send_status_notification = AsyncMock()
    openwb_cp = SimpleNamespace(
        data=SimpleNamespace(get=SimpleNamespace(
            fault_state=0,
            fault_str="",
            ocpp=SimpleNamespace(availability=availability),
        )),
        get_ocpp_status=Mock(return_value=ChargePointStatus.available),
    )
    connection = SimpleNamespace(
        chargebox_id="box-1",
        cp=SimpleNamespace(openwb_cp=openwb_cp),
    )

    asyncio.run(client._send_initial_status_notifications(connection))

    assert client._send_status_notification.await_count == 2
    assert client._send_status_notification.await_args_list[0].args[1] == 0
    assert client._send_status_notification.await_args_list[0].args[4] == controller_status
    assert all(
        call.kwargs["connection"] is connection
        for call in client._send_status_notification.await_args_list
    )


def test_trigger_message_decisions(monkeypatch):
    from control.ocpp import ocpp_chargepoint

    openwb_cp = SimpleNamespace(
        num=1,
        data=SimpleNamespace(get=SimpleNamespace(
            ocpp=SimpleNamespace(availability=[True, True]),
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


@pytest.mark.parametrize(
    "connector_id, expected_notifications",
    [
        (None, [(0, ChargePointStatus.faulted), (1, ChargePointStatus.charging)]),
        (0, [(0, ChargePointStatus.faulted)]),
        (1, [(1, ChargePointStatus.charging)]),
    ],
)
def test_trigger_status_message_after_confirmation(
    monkeypatch,
    connector_id,
    expected_notifications,
):
    from control.ocpp import ocpp_chargepoint

    events = []

    async def send(message):
        events.append(json.loads(message))

    async def call(payload):
        events.append(payload)

    openwb_cp = SimpleNamespace(
        num=1,
        data=SimpleNamespace(get=SimpleNamespace(
            ocpp=SimpleNamespace(availability=[True, True]), fault_state=1, fault_str="error",
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
            connect=AsyncMock(return_value=SimpleNamespace(cp=cp, boot_accepted=True)),
        )
        await cp.route_message(json.dumps([2, "trigger-1", "TriggerMessage", request]))
        await asyncio.sleep(0)

    asyncio.run(check())

    assert events[0] == [3, "trigger-1", {"status": "Accepted"}]
    notifications = events[1:]
    assert [
        (notification.connector_id, notification.status)
        for notification in notifications
    ] == expected_notifications
    assert all(notification.info == "error" for notification in notifications)
    if connector_id in (None, 1):
        openwb_cp.get_ocpp_status.assert_called_once_with()
    else:
        openwb_cp.get_ocpp_status.assert_not_called()


def test_trigger_status_forces_repeat_and_skips_old_connection(monkeypatch):
    from control.ocpp import ocpp_chargepoint

    openwb_cp = SimpleNamespace(
        num=1,
        data=SimpleNamespace(get=SimpleNamespace(
            ocpp=SimpleNamespace(availability=[True, True]), fault_state=0, fault_str="",
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
            connect=AsyncMock(return_value=SimpleNamespace(cp=cp, boot_accepted=True)),
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
            ocpp=SimpleNamespace(availability=[True, True]),
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
        openwb_cp=SimpleNamespace(data=SimpleNamespace(get=SimpleNamespace(ocpp=SimpleNamespace(
            config=SimpleNamespace(MeterValuesSampledData={"value": "Power.Active.Import"}),
        )))),
    )
    client = object.__new__(OcppClient)
    client.connection_manager = SimpleNamespace(
        is_active_charge_point=Mock(return_value=True),
    )
    client._meter_snapshots = (
        {"box-1": SimpleNamespace(connector_id=1, imported=9876, )}
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
            "measurand": "Power.Active.Import",
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


def test_connect_logs_unauthorized_handshake(monkeypatch, caplog):
    ocpp_data = SimpleNamespace(config=SimpleNamespace(active=True))
    monkeypatch.setattr(
        ocpp_connection_manager.data,
        "data",
        SimpleNamespace(optional_data=SimpleNamespace(data=SimpleNamespace(ocpp=ocpp_data))),
    )
    connection_manager = OcppConnectionManager(
        chargepoint_factory=Mock(),
        on_connected=AsyncMock(),
        on_disconnected=AsyncMock(),
    )
    connection_manager.ensure_connected = AsyncMock(
        side_effect=ocpp_connection_manager.InvalidStatusCode(401, {})
    )
    connection_manager._schedule_reconnect = Mock()

    with caplog.at_level(logging.ERROR, logger="control.ocpp.ocpp_connection_manager"):
        result = asyncio.run(connection_manager.connect("box-1"))

    assert result is None
    assert "OCPP-Authentifizierung für box-1 abgelehnt (HTTP 401)" in caplog.text
    assert "Passwort prüfen" in caplog.text
    connection_manager._schedule_reconnect.assert_called_once_with("box-1")


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
    client._set_connected = Mock()

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
    client._set_connected.assert_called_once_with(connection.cp, False)
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
        ocpp=SimpleNamespace(availability=[True, True]),
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
            availability=[True, True],
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
            availability=[True, True],
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
            pending_availability=[False, False],
            pending_transactions=[{
                "action": "stop",
                "transaction_id": 42,
                "id_tag": "TAG",
                "imported": 1234,
                "reason": "EVDisconnected",
            }],
        ))),
    )
    stop_transaction = AsyncMock(return_value=SimpleNamespace(id_tag_info=None))
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


def _make_reset_test_client(monkeypatch, transaction_stopped):
    events = []
    openwb_cp = SimpleNamespace(
        num=1,
        data=SimpleNamespace(get=SimpleNamespace(
            imported=1234,
            plug_state=True,
            ocpp=SimpleNamespace(reset=False),
        )),
        chargepoint_module=SimpleNamespace(config=SimpleNamespace(
            configuration=SimpleNamespace(ip_address="192.0.2.10"),
        )),
    )

    async def stop_and_wait(**_kwargs):
        events.append("stop")
        return transaction_stopped

    async def reconnect_now(chargebox_id):
        events.append("reconnect")
        return SimpleNamespace(chargebox_id=chargebox_id)

    client = object.__new__(OcppClient)
    client.transactions = SimpleNamespace(
        block_start=Mock(),
        stop_and_wait=AsyncMock(side_effect=stop_and_wait),
        get_id_tag=Mock(return_value="TAG"),
        get_state=Mock(return_value=SimpleNamespace(value="IDLE")),
        get_transaction_id=Mock(return_value=42),
    )
    client.connection_manager = SimpleNamespace(
        is_wanted=Mock(return_value=True),
        reconnect_now=AsyncMock(side_effect=reconnect_now),
    )
    monkeypatch.setattr(ocpp_client, "get_cp_from_chargebox_id", lambda _: openwb_cp)

    return client, openwb_cp, events


def test_handle_soft_reset_stops_transaction_before_reconnecting(monkeypatch, mock_pub):
    client, openwb_cp, events = _make_reset_test_client(monkeypatch, transaction_stopped=True)

    asyncio.run(client._handle_reset("box-1", ocpp_client.ResetType.soft))

    assert events == ["stop", "reconnect"]
    client.transactions.stop_and_wait.assert_awaited_once_with(
        chargebox_id="box-1",
        imported=1234,
        id_tag="TAG",
        reason="SoftReset",
    )
    client.connection_manager.reconnect_now.assert_awaited_once_with("box-1")
    assert openwb_cp.data.get.ocpp.reset is True
    mock_pub.pub.assert_called_once_with("openWB/set/chargepoint/1/get/ocpp/reset", True)


def test_handle_hard_reset_publishes_reboot_command(monkeypatch, mock_pub):
    client, openwb_cp, events = _make_reset_test_client(monkeypatch, transaction_stopped=True)
    publish_reboot = Mock()
    monkeypatch.setattr(ocpp_client, "pub_single", publish_reboot)

    asyncio.run(client._handle_reset("box-1", ocpp_client.ResetType.hard))

    assert events == ["stop"]
    client.connection_manager.reconnect_now.assert_not_awaited()
    assert openwb_cp.data.get.ocpp.reset is True
    publish_reboot.assert_called_once_with(
        "openWB/set/command/primary/todo",
        {"command": "systemReboot", "data": {}},
        hostname="192.0.2.10",
    )
    mock_pub.pub.assert_called_once_with("openWB/set/chargepoint/1/get/ocpp/reset", True)


def test_handle_reset_aborts_when_transaction_cannot_be_stopped(monkeypatch, mock_pub):
    client, openwb_cp, events = _make_reset_test_client(monkeypatch, transaction_stopped=False)
    publish_reboot = Mock()
    monkeypatch.setattr(ocpp_client, "pub_single", publish_reboot)

    asyncio.run(client._handle_reset("box-1", ocpp_client.ResetType.hard))

    assert events == ["stop"]
    client.connection_manager.reconnect_now.assert_not_awaited()
    assert openwb_cp.data.get.ocpp.reset is False
    publish_reboot.assert_not_called()
    mock_pub.pub.assert_not_called()


def test_meter_loop_skips_snapshot_for_stale_transaction(monkeypatch):
    chargepoint = SimpleNamespace(
        openwb_cp=SimpleNamespace(data=SimpleNamespace(get=SimpleNamespace(ocpp=SimpleNamespace(
            config=SimpleNamespace(MeterValueSampleInterval={"value": "1"}),
        )))),
        _meter_values=AsyncMock(),
    )
    connection = SimpleNamespace(
        chargebox_id="box-1",
        closing=False,
        boot_accepted=True,
        cp=chargepoint,
    )
    client = object.__new__(OcppClient)
    client.transactions = SimpleNamespace(get_transaction_id=Mock(return_value=123))
    client._meter_snapshots = {
        "box-1": SimpleNamespace(transaction_id=999, connector_id=1, imported=9876),
    }
    sleep_calls = 0

    async def stop_after_stale_snapshot(_interval):
        nonlocal sleep_calls
        sleep_calls += 1
        if sleep_calls == 2:
            connection.closing = True

    monkeypatch.setattr(ocpp_client.asyncio, "sleep", stop_after_stale_snapshot)

    asyncio.run(client._meter_loop(connection))

    client.transactions.get_transaction_id.assert_called_once_with("box-1")
    chargepoint._meter_values.assert_not_awaited()


def test_heartbeat_loop_closes_connection_after_heartbeat_error(monkeypatch):
    chargepoint = SimpleNamespace(
        openwb_cp=SimpleNamespace(data=SimpleNamespace(get=SimpleNamespace(ocpp=SimpleNamespace(
            config=SimpleNamespace(HeartbeatInterval={"value": "1"}),
        )))),
        _heartbeat=AsyncMock(side_effect=RuntimeError("heartbeat failed")),
    )
    websocket = SimpleNamespace(closed=False, close=AsyncMock())
    connection = SimpleNamespace(
        chargebox_id="box-1",
        closing=False,
        boot_accepted=True,
        cp=chargepoint,
        ws=websocket,
    )
    client = object.__new__(OcppClient)

    async def no_wait(_interval):
        return None

    monkeypatch.setattr(ocpp_client.asyncio, "sleep", no_wait)

    asyncio.run(client._heartbeat_loop(connection))

    chargepoint._heartbeat.assert_awaited_once_with()
    websocket.close.assert_awaited_once_with()


def test_connection_closed_removes_only_matching_status_cache(monkeypatch, mock_pub):
    ocpp_data = SimpleNamespace(connected=True)
    chargepoint = SimpleNamespace(
        openwb_num=1,
        openwb_cp=SimpleNamespace(data=SimpleNamespace(get=SimpleNamespace(ocpp=ocpp_data))),
    )
    connection = SimpleNamespace(chargebox_id="box-1", cp=chargepoint)
    client = object.__new__(OcppClient)
    client._last_update = {
        ("box-1", 0): ("status-a", "error-a", ""),
        ("box-1", 1): ("status-b", "error-b", ""),
        ("box-2", 1): ("status-c", "error-c", ""),
    }
    client.transactions = SimpleNamespace(on_disconnected=AsyncMock())
    client.connection_manager = SimpleNamespace(get=lambda _: None)

    asyncio.run(client._connection_closed(connection))

    client.transactions.on_disconnected.assert_awaited_once_with("box-1", connection)
    assert client._last_update == {("box-2", 1): ("status-c", "error-c", "")}
    assert ocpp_data.connected is False
    mock_pub.pub.assert_called_once_with("openWB/set/chargepoint/1/get/ocpp/connected", False)


def test_stale_disconnect_cannot_mark_reconnected_chargepoint_offline(mock_pub):
    ocpp_data = SimpleNamespace(connected=True)
    openwb_cp = SimpleNamespace(data=SimpleNamespace(get=SimpleNamespace(ocpp=ocpp_data)))
    old_cp = SimpleNamespace(openwb_cp=openwb_cp, openwb_num=1)
    new_cp = SimpleNamespace(openwb_cp=openwb_cp, openwb_num=1)
    old_connection = SimpleNamespace(chargebox_id="box-1", cp=old_cp)
    new_connection = SimpleNamespace(chargebox_id="box-1", cp=new_cp)
    client = object.__new__(OcppClient)
    client._last_update = {("box-2", 1): ("some", "status", "")}
    current = [None]
    client.connection_manager = SimpleNamespace(get=lambda _: current[0])

    async def check():
        entered = asyncio.Event()
        resume = asyncio.Event()

        async def delayed_disconnect(chargebox_id, connection):
            entered.set()
            await resume.wait()

        client.transactions = SimpleNamespace(on_disconnected=delayed_disconnect)
        closing = asyncio.create_task(client._connection_closed(old_connection))
        await entered.wait()
        current[0] = new_connection
        client._set_connected(new_cp, True)
        client._last_update[("box-1", 1)] = ("new", "status", "")
        resume.set()
        await closing

    asyncio.run(check())

    assert ocpp_data.connected is True
    assert client._last_update[("box-1", 1)] == ("new", "status", "")
    mock_pub.pub.assert_called_once_with("openWB/set/chargepoint/1/get/ocpp/connected", True)


def test_connection_closed_publishes_disconnected_when_openwb_cp_is_gone(mock_pub):
    chargepoint = SimpleNamespace(openwb_cp=None, openwb_num=1)
    client = object.__new__(OcppClient)

    client._set_connected(chargepoint, False)

    mock_pub.pub.assert_called_once_with("openWB/set/chargepoint/1/get/ocpp/connected", False)
