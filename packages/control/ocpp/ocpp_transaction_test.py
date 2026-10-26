import asyncio
import copy
import json
from dataclasses import asdict
from threading import Event
from types import SimpleNamespace
from unittest.mock import ANY, AsyncMock, call

import pytest
import websockets

from control import data
from control.chargepoint.chargepoint_data import Ocpp, ocpp_config_factory
from control.ocpp import ocpp_client
from control.ocpp import ocpp_chargepoint
from control.ocpp import ocpp_connection_manager
from control.ocpp import ocpp_transaction_coordinator
from control.ocpp.helper import _get_config
from control.ocpp.helper import get_chargebox_id, get_cp_from_chargebox_id
from control.ocpp.ocpp_chargepoint import OcppChargePoint
from control.ocpp.ocpp_client import OcppClient
from control.ocpp.ocpp_connection_manager import OcppConnectionManager
from control.ocpp.ocpp_transaction_coordinator import TransactionCoordinator, TransactionState
from ocpp.v16.enums import (AvailabilityStatus, AvailabilityType, ChargePointStatus,
                            ConfigurationStatus, RegistrationStatus, RemoteStartStopStatus, Action)
from ocpp.v16 import ChargePoint as ServerChargePoint, call_result
from ocpp.routing import on
from helpermodules.setdata import SetData
from helpermodules.subdata import SubData


def ocpp_config_for_test():
    configuration = ocpp_config_factory()
    configuration.TextSetting = {"value": "old", "readonly": False, "type": "str"}
    configuration.EnabledSetting = {"value": False, "readonly": False, "type": "bool"}
    configuration.ScaleSetting = {"value": 1.5, "readonly": False, "type": "float"}
    return configuration


@pytest.fixture
def transaction_setup(monkeypatch):
    openwb_cp = SimpleNamespace(
        num=1,
        data=SimpleNamespace(get=SimpleNamespace(plug_state=True, charge_state=False, imported=100, ocpp=SimpleNamespace(
            transaction_id=None,
            transaction_id_tag=None,
            tag_accepted=False,
            availability=[True, True],
            pending_transactions=[],
            pending_availability=[False, False],
            unlock_stop=False,
            remote_stop=False,
            rfid_stop=False,
        ))),
    )
    charge_point = SimpleNamespace(
        openwb_cp=openwb_cp,
        openwb_num=1,
        transaction_id=None,
        _authorize=AsyncMock(return_value=SimpleNamespace(id_tag_info={"status": "Accepted"})),
        _start_transaction=AsyncMock(return_value=SimpleNamespace(
            id_tag_info={"status": "Accepted"}, transaction_id=42,
        )),
        _stop_transaction=AsyncMock(return_value=SimpleNamespace(id_tag_info=None)),
        apply_pending_availability=AsyncMock(),
    )
    connection = SimpleNamespace(cp=charge_point, boot_accepted=True)
    ensure_connected = AsyncMock(return_value=connection)
    coordinator = TransactionCoordinator(
        ensure_connected=ensure_connected,
    )
    monkeypatch.setattr(ocpp_transaction_coordinator, "get_cp_from_chargebox_id", lambda _: openwb_cp)
    return coordinator, connection, openwb_cp


@pytest.mark.parametrize("availability", [[True, False], [False, True], [False, False]])
def test_transaction_start_rejects_unavailable_connector(transaction_setup, availability):
    coordinator, connection, openwb_cp = transaction_setup
    openwb_cp.data.get.ocpp.availability = availability
    assert asyncio.run(coordinator.start("box-1", 1, "TAG", 0)) is False
    connection.cp._authorize.assert_not_awaited()
    connection.cp._start_transaction.assert_not_awaited()


@pytest.mark.parametrize("stop_flag", ["remote_stop", "rfid_stop", "reset", "unlock_stop"])
def test_stop_flag_blocks_new_transaction_before_connection(transaction_setup, mock_pub, stop_flag):
    coordinator, connection, cp = transaction_setup
    setattr(cp.data.get.ocpp, stop_flag, True)

    assert asyncio.run(coordinator.start("box-1", 1, "TAG", 100)) is False

    coordinator._ensure_connected.assert_not_awaited()
    connection.cp._authorize.assert_not_awaited()
    connection.cp._start_transaction.assert_not_awaited()
    mock_pub.pub.assert_not_called()


def test_start_waits_for_persisted_stop_confirmation(transaction_setup, mock_pub):
    coordinator, connection, cp = transaction_setup
    cp.data.get.ocpp.pending_transactions = [{
        "action": "stop", "transaction_id": 17, "id_tag": "OLD", "imported": 90,
        "reason": "Local", "timestamp": "2026-10-23T12:00:00Z",
    }]

    async def check():
        assert await coordinator.start("box-1", 1, "NEW", 100) is False
        coordinator._ensure_connected.assert_not_awaited()
        connection.cp._authorize.assert_not_awaited()
        connection.cp._start_transaction.assert_not_awaited()

        connection.cp._stop_transaction.return_value = None
        assert await coordinator._replay_persisted_stop_once("box-1", connection) is False
        assert await coordinator.start("box-1", 1, "NEW", 100) is False
        assert cp.data.get.ocpp.pending_transactions
        connection.cp._start_transaction.assert_not_awaited()

        connection.cp._stop_transaction.return_value = SimpleNamespace()
        assert await coordinator._replay_persisted_stop_once("box-1", connection) is True
        assert cp.data.get.ocpp.pending_transactions == []
        assert await coordinator.start("box-1", 1, "NEW", 100) is True

    asyncio.run(check())
    connection.cp._start_transaction.assert_awaited_once()


@pytest.mark.parametrize("confirmed", [False, True])
def test_start_preserves_replay_state_during_connection_setup(transaction_setup, mock_pub, confirmed):
    coordinator, connection, cp = transaction_setup

    async def connect(_):
        cp.data.get.ocpp.pending_transactions = [{
            "action": "stop", "transaction_id": 17, "id_tag": "OLD", "imported": 90,
            "reason": "Local", "timestamp": "2026-10-23T12:00:00Z",
        }]
        connection.cp._stop_transaction.return_value = SimpleNamespace() if confirmed else None
        assert await coordinator._replay_persisted_stop_once("box-1", connection) is confirmed
        return connection

    async def check():
        coordinator._ensure_connected.side_effect = connect
        assert await coordinator.start("box-1", 1, "NEW", 100) is False
        transaction = coordinator._get_transaction("box-1")
        assert transaction.state == (TransactionState.IDLE if confirmed else TransactionState.ERROR)
        assert transaction.transaction_id == (None if confirmed else 17)
        assert bool(cp.data.get.ocpp.pending_transactions) is not confirmed
        connection.cp._authorize.assert_not_awaited()
        connection.cp._start_transaction.assert_not_awaited()

        coordinator._ensure_connected.side_effect = None
        assert await coordinator.start("box-1", 1, "NEW", 100) is confirmed

    asyncio.run(check())


@pytest.mark.parametrize("phase", ["connect", "authorize"])
@pytest.mark.parametrize("replace_transaction", [False, True])
@pytest.mark.parametrize("failure", [False, True])
def test_waiting_start_does_not_change_another_transaction_state(
    transaction_setup, mock_pub, phase, replace_transaction, failure
):
    coordinator, connection, cp = transaction_setup
    transferred = []

    async def take_over(*args, **kwargs):
        transaction = coordinator._get_transaction("box-1")
        if replace_transaction:
            transaction = ocpp_transaction_coordinator.OcppTransaction()
            coordinator._transactions["box-1"] = transaction
        transaction.state = TransactionState.STOPPING
        transaction.transaction_id = 17
        transaction.id_tag = "OLD"
        coordinator._commit("box-1", transaction)
        transferred.append((transaction, vars(transaction).copy(), vars(cp.data.get.ocpp).copy()))
        mock_pub.pub.reset_mock()
        if failure:
            raise ConnectionError("Transport verloren")
        return connection if phase == "connect" else SimpleNamespace(id_tag_info={"status": "Blocked"})

    if phase == "connect":
        coordinator._ensure_connected.side_effect = take_over
    else:
        connection.cp._authorize.side_effect = take_over

    assert asyncio.run(coordinator.start("box-1", 1, "NEW", 100)) is False
    transaction, previous_transaction, previous_model = transferred[0]
    assert vars(transaction) == previous_transaction
    assert vars(cp.data.get.ocpp) == previous_model
    mock_pub.pub.assert_not_called()
    connection.cp._start_transaction.assert_not_awaited()


@pytest.mark.parametrize("phase", ["connect", "authorize"])
@pytest.mark.parametrize("authorization_status", ["Accepted", "Blocked", None])
def test_start_rechecks_persisted_stops_after_waiting(
    transaction_setup, mock_pub, phase, authorization_status
):
    coordinator, connection, cp = transaction_setup
    pending = [{"action": "stop", "transaction_id": 17}]

    async def add_pending(*args, **kwargs):
        cp.data.get.ocpp.pending_transactions = pending
        if phase == "connect":
            return connection
        if authorization_status is None:
            raise ConnectionError("Authorize fehlgeschlagen")
        return SimpleNamespace(id_tag_info={"status": authorization_status})

    if phase == "connect":
        coordinator._ensure_connected.side_effect = add_pending
    else:
        connection.cp._authorize.side_effect = add_pending

    async def check():
        assert await coordinator.start("box-1", 1, "NEW", 100) is False
        assert coordinator.get_state("box-1") == TransactionState.IDLE
        assert cp.data.get.ocpp.pending_transactions == pending
        assert await coordinator.start("box-1", 1, "NEW", 100) is False

    asyncio.run(check())
    connection.cp._start_transaction.assert_not_awaited()


def test_rfid_stop_waits_for_hardware_and_uses_current_model_meter(transaction_setup, mock_pub, monkeypatch):
    coordinator, connection, cp = transaction_setup
    cp.data.get.ocpp.transaction_id = 42
    cp.data.get.ocpp.transaction_id_tag = "TAG"
    cp.data.get.charge_state = True
    current = [cp]
    monkeypatch.setattr(ocpp_transaction_coordinator, "get_cp_from_chargebox_id", lambda _: current[0])
    final_time = "2026-10-23T12:00:30Z"

    async def authorize(**kwargs):
        cp.data.get.imported = 120
        return SimpleNamespace(id_tag_info={"status": "Accepted"})

    async def hardware_tick(interval):
        assert interval == 0.5
        assert coordinator.get_state("box-1") == TransactionState.STOPPING
        assert cp.data.get.ocpp.tag_accepted is False
        assert cp.data.get.ocpp.rfid_stop is True
        connection.cp._stop_transaction.assert_not_awaited()
        current[0] = copy.deepcopy(cp)
        current[0].data.get.imported = 125.9
        current[0].data.get.charge_state = False
        monkeypatch.setattr(ocpp_transaction_coordinator, "_get_formatted_time", lambda: final_time)

    connection.cp._authorize.side_effect = authorize
    monkeypatch.setattr(ocpp_transaction_coordinator.asyncio, "sleep", hardware_tick)
    assert asyncio.run(coordinator.stop("box-1", 100, "TAG", "Local", authorize_stop=True)) is True
    connection.cp._stop_transaction.assert_awaited_once_with(
        meter_stop=125, transaction_id=42, reason="Local", id_tag="TAG", timestamp=final_time,
    )


@pytest.mark.parametrize("failure", ["charging", "fault", "read_error", "invalid_meter"])
def test_stop_meter_timeout_uses_last_valid_value_and_keeps_local_block(
    transaction_setup, mock_pub, monkeypatch, caplog, failure
):
    coordinator, connection, cp = transaction_setup
    cp.data.get.ocpp.transaction_id = 42
    cp.data.get.ocpp.transaction_id_tag = "TAG"
    cp.data.get.ocpp.remote_stop = True
    cp.data.get.charge_state = failure == "charging"
    cp.data.get.fault_state = 2 if failure == "fault" else 0
    cp.data.get.error_timestamp = 123 if failure == "read_error" else None
    cp.data.get.imported = float("nan") if failure == "invalid_meter" else 110
    clock = [0.0]
    sleeps = []
    monkeypatch.setattr(ocpp_transaction_coordinator, "monotonic", lambda: clock[0])
    monkeypatch.setattr(ocpp_transaction_coordinator, "_get_formatted_time", lambda: f"time-{clock[0]}")

    async def tick(interval):
        sleeps.append(interval)
        clock[0] += interval
        assert cp.data.get.ocpp.tag_accepted is False
        connection.cp._stop_transaction.assert_not_awaited()
        if failure != "invalid_meter":
            cp.data.get.imported = 120 if clock[0] < 30 else float("nan")

    monkeypatch.setattr(ocpp_transaction_coordinator.asyncio, "sleep", tick)
    assert asyncio.run(coordinator.stop("box-1", 100, "TAG", "Remote")) is True
    assert clock[0] == 30
    assert len(sleeps) == 60
    connection.cp._stop_transaction.assert_awaited_once_with(
        meter_stop=100 if failure == "invalid_meter" else 120,
        transaction_id=42, reason="Remote", id_tag="TAG", timestamp="time-30.0",
    )
    assert "Ladestopp nach 30 s nicht zuverlässig bestätigt" in caplog.text
    assert cp.data.get.ocpp.remote_stop is True
    assert cp.data.get.ocpp.tag_accepted is False


def test_paused_transaction_stop_uses_current_meter_without_waiting(transaction_setup, mock_pub, monkeypatch):
    coordinator, connection, cp = transaction_setup
    cp.data.get.ocpp.transaction_id = 42
    cp.data.get.imported = 140
    sleep = AsyncMock()
    monkeypatch.setattr(ocpp_transaction_coordinator.asyncio, "sleep", sleep)

    assert asyncio.run(coordinator.stop("box-1", 100, "TAG", "Local")) is True
    sleep.assert_not_awaited()
    assert connection.cp._stop_transaction.await_args.kwargs["meter_stop"] == 140


def test_offline_stop_finalizes_meter_once_and_replay_does_not_wait(transaction_setup, mock_pub, monkeypatch):
    coordinator, connection, cp = transaction_setup
    cp.data.get.ocpp.transaction_id = 42
    cp.data.get.ocpp.transaction_id_tag = "TAG"
    cp.data.get.charge_state = True
    coordinator._ensure_connected.return_value = None
    final_time = "2026-10-23T12:00:30Z"

    async def tick(_):
        cp.data.get.charge_state = False
        cp.data.get.imported = 135
        monkeypatch.setattr(ocpp_transaction_coordinator, "_get_formatted_time", lambda: final_time)

    monkeypatch.setattr(ocpp_transaction_coordinator.asyncio, "sleep", tick)

    async def check():
        assert await coordinator.stop("box-1", 100, "TAG", "Local", authorize_stop=True) is True
        assert cp.data.get.ocpp.pending_transactions[0]["imported"] == 135
        assert cp.data.get.ocpp.pending_transactions[0]["timestamp"] == final_time
        connection.cp._stop_transaction.assert_not_awaited()
        cp.data.get.imported = 999
        cp.data.get.charge_state = True
        sleep = AsyncMock()
        monkeypatch.setattr(ocpp_transaction_coordinator.asyncio, "sleep", sleep)
        assert await coordinator._replay_persisted_stop_once("box-1", connection) is True
        sleep.assert_not_awaited()

    asyncio.run(check())
    connection.cp._stop_transaction.assert_awaited_once_with(
        meter_stop=135, transaction_id=42, reason="Local", id_tag="TAG", timestamp=final_time,
    )


def test_direct_stop_retry_keeps_final_meter_and_timestamp(transaction_setup, mock_pub, monkeypatch):
    coordinator, connection, cp = transaction_setup
    cp.data.get.ocpp.transaction_id = 42
    cp.data.get.imported = 140
    connection.cp._stop_transaction.side_effect = [ConnectionError("Antwort fehlt"), SimpleNamespace()]
    monkeypatch.setattr(coordinator, "_schedule_replay_retry", lambda *_: None)
    monkeypatch.setattr(ocpp_transaction_coordinator, "_get_formatted_time", lambda: "first-stop-time")

    async def check():
        assert await coordinator.stop("box-1", 100, "TAG", "Remote") is False
        cp.data.get.imported = 999
        cp.data.get.charge_state = True
        monkeypatch.setattr(ocpp_transaction_coordinator, "_get_formatted_time", lambda: "later-time")
        sleep = AsyncMock()
        monkeypatch.setattr(ocpp_transaction_coordinator.asyncio, "sleep", sleep)
        assert await coordinator.stop("box-1", 999, "OTHER", "Other") is True
        sleep.assert_not_awaited()

    asyncio.run(check())
    assert connection.cp._stop_transaction.await_args_list == [call(
        meter_stop=140, transaction_id=42, reason="Remote", id_tag="TAG", timestamp="first-stop-time",
    )] * 2


@pytest.mark.parametrize("status", ["Accepted", "Blocked", None])
@pytest.mark.parametrize("active", [False, True])
def test_standalone_authorize_preserves_transaction(transaction_setup, mock_pub, status, active):
    coordinator, connection, openwb_cp = transaction_setup
    transaction = coordinator._get_transaction("box-1")
    if active:
        transaction.state = TransactionState.ACTIVE
        transaction.transaction_id = 42
        transaction.id_tag = "ORIGINAL"
        coordinator._commit("box-1", transaction)
    previous_transaction = vars(transaction).copy()
    previous_ocpp = vars(openwb_cp.data.get.ocpp).copy()
    mock_pub.pub.reset_mock()
    connection.cp._authorize.return_value = SimpleNamespace(id_tag_info={"status": status})

    result = asyncio.run(coordinator.authorize("box-1", "OTHER"))

    assert result.accepted is (status == "Accepted")
    assert result.status == status
    assert result.error is None
    assert vars(transaction) == previous_transaction
    assert vars(openwb_cp.data.get.ocpp) == previous_ocpp
    connection.cp._authorize.assert_awaited_once_with(id_tag="OTHER")
    connection.cp._start_transaction.assert_not_awaited()
    connection.cp._stop_transaction.assert_not_awaited()
    mock_pub.pub.assert_not_called()


@pytest.mark.parametrize("response", [None, SimpleNamespace(), SimpleNamespace(id_tag_info=None)])
def test_standalone_authorize_missing_response_is_not_accepted(transaction_setup, response):
    coordinator, connection, _ = transaction_setup
    connection.cp._authorize.return_value = response

    result = asyncio.run(coordinator.authorize("box-1", "TAG"))

    assert result.accepted is False
    assert result.status is None
    assert result.error is None


@pytest.mark.parametrize("chargebox_id,id_tag", [("", "TAG"), ("box-1", "")])
def test_standalone_authorize_requires_inputs(transaction_setup, chargebox_id, id_tag):
    coordinator, connection, _ = transaction_setup

    result = asyncio.run(coordinator.authorize(chargebox_id, id_tag))

    assert result.accepted is False
    assert result.error is not None
    coordinator._ensure_connected.assert_not_awaited()
    connection.cp._authorize.assert_not_awaited()


@pytest.mark.parametrize("failure", ["offline", "boot", "connect", "authorize"])
def test_standalone_authorize_reports_errors_without_transaction_changes(transaction_setup, mock_pub, failure):
    coordinator, connection, openwb_cp = transaction_setup
    transaction = coordinator._get_transaction("box-1")
    previous_transaction = vars(transaction).copy()
    previous_ocpp = vars(openwb_cp.data.get.ocpp).copy()
    if failure == "offline":
        coordinator._ensure_connected.return_value = None
    elif failure == "boot":
        connection.boot_accepted = False
    elif failure == "connect":
        coordinator._ensure_connected.side_effect = RuntimeError("connect failed")
    else:
        connection.cp._authorize.side_effect = RuntimeError("authorize failed")

    result = asyncio.run(coordinator.authorize("box-1", "TAG"))

    assert result.accepted is False
    assert result.error is not None
    assert vars(transaction) == previous_transaction
    assert vars(openwb_cp.data.get.ocpp) == previous_ocpp
    connection.cp._start_transaction.assert_not_awaited()
    connection.cp._stop_transaction.assert_not_awaited()
    mock_pub.pub.assert_not_called()
    if failure != "authorize":
        connection.cp._authorize.assert_not_awaited()


@pytest.mark.parametrize("cancel_during", ["connect", "authorize"])
def test_standalone_authorize_propagates_cancellation(transaction_setup, mock_pub, cancel_during):
    coordinator, connection, _ = transaction_setup
    pending = coordinator._ensure_connected if cancel_during == "connect" else connection.cp._authorize
    pending.side_effect = asyncio.CancelledError()

    with pytest.raises(asyncio.CancelledError):
        asyncio.run(coordinator.authorize("box-1", "TAG"))

    assert coordinator._transactions == {}
    connection.cp._start_transaction.assert_not_awaited()
    connection.cp._stop_transaction.assert_not_awaited()
    mock_pub.pub.assert_not_called()


def test_start_authorize_error_returns_to_idle(transaction_setup):
    coordinator, connection, openwb_cp = transaction_setup
    connection.cp._authorize.side_effect = RuntimeError()

    assert asyncio.run(coordinator.start("box-1", 1, "TAG", 100)) is False

    transaction = coordinator._get_transaction("box-1")
    assert transaction.state == TransactionState.IDLE
    assert transaction.last_error == ""
    assert transaction.pending_stop is None
    assert openwb_cp.data.get.ocpp.tag_accepted is False
    connection.cp._start_transaction.assert_not_awaited()


def test_start_publishes_active_transaction(transaction_setup, mock_pub):
    coordinator, connection, openwb_cp = transaction_setup

    result = asyncio.run(coordinator.start("box-1", 1, "TAG", 100))

    assert result is True
    assert coordinator.get_state("box-1") == TransactionState.ACTIVE
    assert coordinator.get_transaction_id("box-1") == 42
    assert openwb_cp.data.get.ocpp.transaction_id == 42
    assert openwb_cp.data.get.ocpp.tag_accepted is True
    connection.cp._authorize.assert_awaited_once_with(id_tag="TAG")
    coordinator._ensure_connected.assert_awaited_once_with("box-1")
    connection.cp._start_transaction.assert_awaited_once_with(
        connector_id=1, id_tag="TAG", imported=100,
    )
    mock_pub.pub.assert_any_call("openWB/set/chargepoint/1/get/ocpp/transaction_id", 42)


@pytest.mark.parametrize("rejected_step", ["authorize", "start"])
def test_rejected_start_does_not_release_charging(transaction_setup, rejected_step):
    coordinator, connection, openwb_cp = transaction_setup
    response = SimpleNamespace(id_tag_info={"status": "Blocked"}, transaction_id=None)
    if rejected_step == "authorize":
        connection.cp._authorize.return_value = response
    else:
        connection.cp._start_transaction.return_value = response

    assert asyncio.run(coordinator.start("box-1", 1, "TAG", 100)) is False

    assert coordinator.get_state("box-1") == TransactionState.REJECTED
    assert openwb_cp.data.get.ocpp.tag_accepted is False
    assert openwb_cp.data.get.ocpp.transaction_id is None
    if rejected_step == "authorize":
        connection.cp._start_transaction.assert_not_awaited()


@pytest.mark.parametrize("failure", ["timeout", "connection", "missing_response", "missing_id"])
def test_unconfirmed_start_blocks_session_and_allows_retry_after_unplug(transaction_setup, caplog, failure):
    coordinator, connection, openwb_cp = transaction_setup
    if failure == "timeout":
        connection.cp._start_transaction.side_effect = asyncio.TimeoutError("response lost")
    elif failure == "connection":
        connection.cp._start_transaction.side_effect = ConnectionError("disconnected")
    elif failure == "missing_response":
        connection.cp._start_transaction.return_value = None
    else:
        connection.cp._start_transaction.return_value = SimpleNamespace(
            id_tag_info={"status": "Accepted"}, transaction_id=None,
        )

    async def check():
        assert await coordinator.start("box-1", 1, "TAG", 100) is False
        assert coordinator.get_state("box-1") == TransactionState.START_UNCONFIRMED
        assert openwb_cp.data.get.ocpp.authorization_flow_status == "start_unconfirmed"
        assert openwb_cp.data.get.ocpp.tag_accepted is False
        assert await coordinator.start("box-1", 1, "TAG", 100) is False
        assert await coordinator.start("box-1", 1, "OTHER-TAG", 100) is False
        assert await coordinator.stop("box-1", 100) is False
        connection.cp._authorize.assert_awaited_once()
        connection.cp._start_transaction.assert_awaited_once()
        connection.cp._stop_transaction.assert_not_awaited()

        openwb_cp.data.get.plug_state = False
        assert coordinator.clear_start_block("box-1") is True
        assert coordinator.get_state("box-1") == TransactionState.IDLE
        assert openwb_cp.data.get.ocpp.authorization_flow_status is None
        assert coordinator.get_transaction_id("box-1") is None
        assert coordinator.get_id_tag("box-1") is None
        assert coordinator._get_transaction("box-1").pending_stop is None
        assert coordinator.clear_start_block("box-1") is False

        openwb_cp.data.get.plug_state = True
        connection.cp._start_transaction.side_effect = None
        connection.cp._start_transaction.return_value = SimpleNamespace(
            id_tag_info={"status": "Accepted"}, transaction_id=43,
        )
        assert await coordinator.start("box-1", 1, "TAG", 110) is True

    asyncio.run(check())

    assert coordinator.get_state("box-1") == TransactionState.ACTIVE
    assert coordinator.get_transaction_id("box-1") == 43
    assert connection.cp._start_transaction.await_count == 2
    connection.cp._stop_transaction.assert_not_awaited()
    assert "serverseitige Transaktionszustand ist unbekannt" in caplog.text
    assert "nach Abstecken lokal zurückgesetzt" in caplog.text


def test_unconfirmed_start_survives_reconnect_and_backend_restart(transaction_setup):
    coordinator, connection, openwb_cp = transaction_setup
    connection.cp._start_transaction.side_effect = asyncio.TimeoutError()

    async def check():
        assert await coordinator.start("box-1", 1, "TAG", 100) is False
        await coordinator.on_disconnected("box-1", connection)
        await coordinator.on_connected("box-1", connection)
        assert await coordinator.start("box-1", 1, "TAG", 100) is False

        restored = TransactionCoordinator(
            ensure_connected=coordinator._ensure_connected,
        )
        assert restored.get_state("box-1") == TransactionState.START_UNCONFIRMED
        assert await restored.start("box-1", 1, "OTHER-TAG", 100) is False
        openwb_cp.data.get.plug_state = False
        assert restored.clear_start_block("box-1") is True
        assert openwb_cp.data.get.ocpp.authorization_flow_status is None

    asyncio.run(check())
    connection.cp._start_transaction.assert_awaited_once()


@pytest.mark.parametrize("flow_status", ["start_pending", "start_authorizing"])
def test_restart_clears_stale_phase_before_start_was_sent(transaction_setup, mock_pub, caplog, flow_status):
    coordinator, connection, openwb_cp = transaction_setup
    openwb_cp.data.get.ocpp.authorization_flow_status = flow_status

    assert coordinator.get_state("box-1") == TransactionState.IDLE
    assert openwb_cp.data.get.ocpp.authorization_flow_status is None
    assert openwb_cp.data.get.ocpp.tag_accepted is False
    assert openwb_cp.data.get.ocpp.transaction_id is None
    mock_pub.pub.assert_any_call("openWB/set/chargepoint/1/get/ocpp/authorization_flow_status", None)
    assert flow_status in caplog.text
    assert "nach Backend-Neustart zurückgesetzt" in caplog.text

    calls = mock_pub.pub.call_count
    assert coordinator.get_transaction_id("box-1") is None
    assert coordinator.get_state("box-1") == TransactionState.IDLE
    assert mock_pub.pub.call_count == calls
    assert asyncio.run(coordinator.start("box-1", 1, "TAG", 100)) is True
    connection.cp._authorize.assert_awaited_once_with(id_tag="TAG")
    connection.cp._start_transaction.assert_awaited_once_with(connector_id=1, id_tag="TAG", imported=100)


def test_restart_during_start_requires_unplug_before_retry(transaction_setup, mock_pub, caplog):
    coordinator, connection, openwb_cp = transaction_setup
    openwb_cp.data.get.ocpp.authorization_flow_status = "start_starting"

    async def check():
        assert coordinator.get_state("box-1") == TransactionState.START_UNCONFIRMED
        assert openwb_cp.data.get.ocpp.authorization_flow_status == "start_unconfirmed"
        assert openwb_cp.data.get.ocpp.tag_accepted is False
        assert coordinator.get_transaction_id("box-1") is None
        assert await coordinator.start("box-1", 1, "TAG", 100) is False
        assert await coordinator.start("box-1", 1, "OTHER-TAG", 100) is False
        connection.cp._authorize.assert_not_awaited()
        connection.cp._start_transaction.assert_not_awaited()

        openwb_cp.data.get.plug_state = False
        assert coordinator.clear_start_block("box-1") is True
        assert openwb_cp.data.get.ocpp.authorization_flow_status is None
        openwb_cp.data.get.plug_state = True
        assert await coordinator.start("box-1", 1, "TAG", 100) is True

    asyncio.run(check())
    mock_pub.pub.assert_any_call("openWB/set/chargepoint/1/get/ocpp/authorization_flow_status", "start_unconfirmed")
    assert "Backend während StartTransaction neu gestartet" in caplog.text
    assert "serverseitige Transaktionszustand ist unbekannt" in caplog.text
    connection.cp._start_transaction.assert_awaited_once()
    connection.cp._stop_transaction.assert_not_awaited()


@pytest.mark.parametrize("flow_status", ["start_pending", "start_authorizing", "start_starting"])
def test_restart_preserves_known_transaction_over_stale_phase(transaction_setup, mock_pub, flow_status):
    coordinator, connection, openwb_cp = transaction_setup
    openwb_cp.data.get.ocpp.transaction_id = 42
    openwb_cp.data.get.ocpp.transaction_id_tag = "ACTIVE-TAG"
    openwb_cp.data.get.ocpp.authorization_flow_status = flow_status

    async def check():
        assert coordinator.get_state("box-1") == TransactionState.ACTIVE
        assert coordinator.get_transaction_id("box-1") == 42
        assert coordinator.get_id_tag("box-1") == "ACTIVE-TAG"
        assert await coordinator.start("box-1", 1, "NEW-TAG", 100) is True

    asyncio.run(check())
    assert openwb_cp.data.get.ocpp.transaction_id == 42
    connection.cp._authorize.assert_not_awaited()
    connection.cp._start_transaction.assert_not_awaited()
    mock_pub.pub.assert_not_called()


@pytest.mark.parametrize("waiting_for,expected_state,flow_status", [
    ("connect", TransactionState.START_PENDING, "start_pending"),
    ("authorize", TransactionState.AUTHORIZING, "start_authorizing"),
    ("start", TransactionState.STARTING, "start_starting"),
])
def test_reconnect_does_not_reset_live_start(transaction_setup, mock_pub, waiting_for, expected_state, flow_status):
    coordinator, connection, openwb_cp = transaction_setup
    waiting = (coordinator._ensure_connected if waiting_for == "connect" else
               getattr(connection.cp, "_authorize" if waiting_for == "authorize" else "_start_transaction"))

    async def check():
        entered = asyncio.Event()
        release = asyncio.Event()

        async def delayed(*args, **kwargs):
            entered.set()
            await release.wait()
            return waiting.return_value

        waiting.side_effect = delayed
        start = asyncio.create_task(coordinator.start("box-1", 1, "TAG", 100))
        await asyncio.wait_for(entered.wait(), 5)
        calls = mock_pub.pub.call_count
        await coordinator.on_connected("box-1", connection)
        assert coordinator.get_state("box-1") == expected_state
        assert coordinator.get_transaction_id("box-1") is None
        assert openwb_cp.data.get.ocpp.authorization_flow_status == flow_status
        assert mock_pub.pub.call_count == calls
        assert not start.done()
        release.set()
        assert await asyncio.wait_for(start, 5) is True

    asyncio.run(check())
    assert coordinator.get_state("box-1") == TransactionState.ACTIVE
    connection.cp._start_transaction.assert_awaited_once()


@pytest.mark.parametrize("state,transaction_id", [
    (TransactionState.ACTIVE, 42), (TransactionState.ERROR, 42), (TransactionState.STARTING, None),
])
def test_unplug_does_not_forget_known_or_pending_transaction(transaction_setup, mock_pub, state, transaction_id):
    coordinator, _, openwb_cp = transaction_setup
    transaction = coordinator._get_transaction("box-1")
    transaction.state = state
    transaction.transaction_id = transaction_id
    openwb_cp.data.get.plug_state = False
    mock_pub.reset_mock()

    assert coordinator.clear_start_block("box-1") is False
    assert transaction.state == state
    assert transaction.transaction_id == transaction_id
    mock_pub.pub.assert_not_called()


@pytest.mark.parametrize("waiting_for", ["connect", "authorize", "start"])
def test_stop_during_start_is_not_lost(transaction_setup, mock_pub, monkeypatch, waiting_for):
    coordinator, connection, openwb_cp = transaction_setup
    original = (coordinator._ensure_connected if waiting_for == "connect" else
                getattr(connection.cp, "_authorize" if waiting_for == "authorize" else "_start_transaction"))
    event_time = "2026-10-23T12:00:00Z"
    monkeypatch.setattr(ocpp_transaction_coordinator, "_get_formatted_time", lambda: event_time)

    async def check():
        entered = asyncio.Event()
        release = asyncio.Event()

        async def delayed(*args, **kwargs):
            entered.set()
            await release.wait()
            return original.return_value

        original.side_effect = delayed
        start = asyncio.create_task(coordinator.start("box-1", 1, "TAG", 100))
        try:
            await asyncio.wait_for(entered.wait(), timeout=5)
        except asyncio.TimeoutError:
            if start.done():
                await start
            raise
        assert openwb_cp.data.get.ocpp.tag_accepted is False
        assert await coordinator.stop("box-1", 150, "", "EVDisconnected") is False
        monkeypatch.setattr(ocpp_transaction_coordinator, "_get_formatted_time",
                            lambda: "2026-10-23T12:01:00Z")
        release.set()
        assert await start is False

    asyncio.run(check())

    if waiting_for != "start":
        connection.cp._start_transaction.assert_not_awaited()
        connection.cp._stop_transaction.assert_not_awaited()
        if waiting_for == "connect":
            connection.cp._authorize.assert_not_awaited()
    else:
        connection.cp._stop_transaction.assert_awaited_once_with(
            meter_stop=150, transaction_id=42, reason="EVDisconnected", id_tag="TAG",
            timestamp="2026-10-23T12:01:00Z",
        )
    assert coordinator.get_state("box-1") == TransactionState.IDLE
    assert openwb_cp.data.get.ocpp.transaction_id is None
    assert openwb_cp.data.get.ocpp.tag_accepted is False
    assert call("openWB/set/chargepoint/1/get/ocpp/tag_accepted", True) not in mock_pub.pub.call_args_list


@pytest.mark.parametrize("waiting_for", ["connect", "authorize"])
@pytest.mark.parametrize("abort", ["unplug", "block", "unavailable", "remote_stop", "rfid_stop", "reset", "unlock_stop"])
def test_start_rechecks_conditions_after_waiting(transaction_setup, mock_pub, waiting_for, abort):
    coordinator, connection, openwb_cp = transaction_setup

    async def check():
        entered = asyncio.Event()
        release = asyncio.Event()
        waiting = coordinator._ensure_connected if waiting_for == "connect" else connection.cp._authorize

        async def delayed(*args, **kwargs):
            entered.set()
            await release.wait()
            return waiting.return_value

        waiting.side_effect = delayed
        start = asyncio.create_task(coordinator.start("box-1", 1, "TAG", 100))
        await asyncio.wait_for(entered.wait(), 5)
        if abort == "unplug":
            openwb_cp.data.get.plug_state = False
        elif abort == "block":
            coordinator.block_start("box-1")
        elif abort == "unavailable":
            openwb_cp.data.get.ocpp.availability = [True, False]
        else:
            setattr(openwb_cp.data.get.ocpp, abort, True)
        release.set()
        assert await start is False

    asyncio.run(check())
    connection.cp._start_transaction.assert_not_awaited()
    connection.cp._stop_transaction.assert_not_awaited()
    if waiting_for == "connect":
        connection.cp._authorize.assert_not_awaited()
    assert coordinator.get_state("box-1") == TransactionState.IDLE
    assert call("openWB/set/chargepoint/1/get/ocpp/tag_accepted", True) not in mock_pub.pub.call_args_list


def test_start_rechecks_current_model_after_authorize(transaction_setup, monkeypatch):
    coordinator, connection, openwb_cp = transaction_setup

    async def authorize(**kwargs):
        current_cp = copy.deepcopy(openwb_cp)
        current_cp.data.get.plug_state = False
        monkeypatch.setattr(ocpp_transaction_coordinator, "get_cp_from_chargebox_id", lambda _: current_cp)
        return connection.cp._authorize.return_value

    connection.cp._authorize.side_effect = authorize
    assert asyncio.run(coordinator.start("box-1", 1, "TAG", 100)) is False
    connection.cp._start_transaction.assert_not_awaited()
    assert coordinator.get_state("box-1") == TransactionState.IDLE


@pytest.mark.parametrize("abort,reason", [("unplug", "EVDisconnected"), ("block", "Other"),
                                         ("unavailable", "Other"), ("unlock", "UnlockCommand"),
                                         ("remote", "Remote"), ("rfid_stop", "Other"), ("reset", "Other")])
@pytest.mark.parametrize("stop_fails", [False, True])
def test_abort_during_start_confirmation_stops_without_releasing_charging(
        transaction_setup, mock_pub, monkeypatch, abort, reason, stop_fails):
    coordinator, connection, openwb_cp = transaction_setup
    stop_time = "2026-10-23T12:00:00Z"
    monkeypatch.setattr(ocpp_transaction_coordinator, "_get_formatted_time", lambda: stop_time)

    async def check():
        entered = asyncio.Event()
        release = asyncio.Event()

        async def delayed_start(**kwargs):
            entered.set()
            await release.wait()
            return connection.cp._start_transaction.return_value

        connection.cp._start_transaction.side_effect = delayed_start
        if stop_fails:
            connection.cp._stop_transaction.side_effect = ConnectionError("stop response lost")
        start = asyncio.create_task(coordinator.start("box-1", 1, "TAG", 100))
        await asyncio.wait_for(entered.wait(), 5)
        openwb_cp.data.get.imported = 175
        if abort == "unplug":
            openwb_cp.data.get.plug_state = False
        elif abort == "unavailable":
            openwb_cp.data.get.ocpp.availability = [False, True]
        elif abort == "block":
            coordinator.block_start("box-1")
        else:
            flag = {"unlock": "unlock_stop", "remote": "remote_stop"}.get(abort, abort)
            setattr(openwb_cp.data.get.ocpp, flag, True)
        release.set()
        assert await start is False
        if stop_fails:
            assert "box-1" in coordinator._replay_tasks
            await coordinator.on_disconnected("box-1", connection)

    asyncio.run(check())
    connection.cp._stop_transaction.assert_awaited_once_with(
        meter_stop=175, transaction_id=42, reason=reason, id_tag="TAG", timestamp=stop_time,
    )
    assert openwb_cp.data.get.ocpp.tag_accepted is False
    assert call("openWB/set/chargepoint/1/get/ocpp/tag_accepted", True) not in mock_pub.pub.call_args_list
    if stop_fails:
        assert coordinator.get_state("box-1") == TransactionState.ERROR
        assert coordinator.get_transaction_id("box-1") == 42
        assert openwb_cp.data.get.ocpp.transaction_id is None
        assert openwb_cp.data.get.ocpp.pending_transactions == [{
            "action": "stop", "transaction_id": 42, "id_tag": "TAG", "imported": 175,
            "reason": reason, "timestamp": stop_time,
        }]
    else:
        assert coordinator.get_state("box-1") == TransactionState.IDLE
        assert coordinator.get_transaction_id("box-1") is None
        assert openwb_cp.data.get.ocpp.pending_transactions == []


def test_rfid_stop_authorizes_before_stopping(transaction_setup):
    coordinator, connection, _ = transaction_setup

    async def check():
        assert await coordinator.start("box-1", 1, "START_TAG", 100)
        connection.cp._authorize.reset_mock()

        async def authorize(**kwargs):
            assert coordinator.get_state("box-1") == TransactionState.ACTIVE
            connection.cp._stop_transaction.assert_not_awaited()
            return SimpleNamespace(id_tag_info={"status": "Accepted"})

        connection.cp._authorize.side_effect = authorize
        assert await coordinator.stop("box-1", 150, "STOP_TAG", "Local", authorize_stop=True)

    asyncio.run(check())

    connection.cp._authorize.assert_awaited_once_with(id_tag="STOP_TAG")
    connection.cp._stop_transaction.assert_awaited_once_with(
        meter_stop=150, transaction_id=42, reason="Local", id_tag="STOP_TAG", timestamp=ANY,
    )
    assert coordinator.get_state("box-1") == TransactionState.IDLE


@pytest.mark.parametrize("failure", ["blocked", "error", "empty", "offline", "boot", "cancel"])
def test_rfid_stop_auth_failure_preserves_active_transaction(transaction_setup, mock_pub, failure):
    coordinator, connection, openwb_cp = transaction_setup

    async def check():
        assert await coordinator.start("box-1", 1, "START_TAG", 100)
        transaction = coordinator._get_transaction("box-1")
        previous_transaction = vars(transaction).copy()
        previous_ocpp = vars(openwb_cp.data.get.ocpp).copy()
        mock_pub.pub.reset_mock()
        connection.cp._authorize.reset_mock()
        if failure == "blocked":
            connection.cp._authorize.return_value = SimpleNamespace(id_tag_info={"status": "Blocked"})
        elif failure == "error":
            connection.cp._authorize.side_effect = RuntimeError("authorize failed")
        elif failure == "offline":
            coordinator._ensure_connected.return_value = None
        elif failure == "boot":
            connection.boot_accepted = False
        elif failure == "cancel":
            connection.cp._authorize.side_effect = asyncio.CancelledError()

        request = coordinator.stop("box-1", 150, "" if failure == "empty" else "STOP_TAG",
                                   "Local", authorize_stop=True)
        if failure == "cancel":
            with pytest.raises(asyncio.CancelledError):
                await request
        else:
            assert await request is False

        assert vars(transaction) == previous_transaction
        assert vars(openwb_cp.data.get.ocpp) == previous_ocpp
        mock_pub.pub.assert_not_called()

    asyncio.run(check())

    connection.cp._stop_transaction.assert_not_awaited()
    if failure in ("empty", "offline", "boot"):
        connection.cp._authorize.assert_not_awaited()


@pytest.mark.parametrize("transport", ["missing", "closing", "closed"])
def test_same_tag_rfid_stop_is_accepted_offline_and_replayed(transaction_setup, mock_pub, caplog, transport):
    coordinator, connection, cp = transaction_setup

    async def check():
        assert await coordinator.start("box-1", 1, "TAG", 100)
        connection.cp._authorize.reset_mock()
        coordinator._ensure_connected.reset_mock()
        connection.closing = transport == "closing"
        connection.ws = SimpleNamespace(closed=transport == "closed")
        coordinator._ensure_connected.return_value = None if transport == "missing" else connection

        assert await coordinator.stop("box-1", 150, "TAG", "Local", authorize_stop=True) is True
        coordinator._ensure_connected.assert_awaited_once_with("box-1")
        connection.cp._authorize.assert_not_awaited()
        connection.cp._stop_transaction.assert_not_awaited()
        assert cp.data.get.ocpp.rfid_stop is True
        assert cp.data.get.ocpp.tag_accepted is False
        assert cp.data.get.ocpp.transaction_id is None
        pending = cp.data.get.ocpp.pending_transactions[0]
        assert pending["transaction_id"] == 42
        assert pending["id_tag"] == "TAG"
        assert pending["reason"] == "Local"
        assert pending["imported"] == 150
        assert coordinator.get_state("box-1") == TransactionState.STOPPING

        connection.closing = connection.ws.closed = False
        coordinator._ensure_connected.return_value = connection
        await coordinator.on_connected("box-1", connection)
        connection.cp._stop_transaction.assert_awaited_once_with(
            meter_stop=150, transaction_id=42, reason="Local", id_tag="TAG", timestamp=pending["timestamp"],
        )
        assert cp.data.get.ocpp.pending_transactions == []
        assert cp.data.get.ocpp.rfid_stop is True
        assert coordinator.get_state("box-1") == TransactionState.IDLE

    asyncio.run(check())
    mock_pub.pub.assert_any_call("openWB/set/chargepoint/1/get/ocpp/rfid_stop", True)
    assert "offline lokal angenommen" in caplog.text


@pytest.mark.parametrize("connected_after_attempt", [False, True])
def test_rfid_stop_waits_for_connection_attempt_before_offline_fallback(transaction_setup, connected_after_attempt):
    coordinator, connection, cp = transaction_setup

    async def check():
        assert await coordinator.start("box-1", 1, "TAG", 100)
        connection.cp._authorize.reset_mock()
        entered = asyncio.Event()
        release = asyncio.Event()

        async def connect(chargebox_id):
            entered.set()
            await release.wait()
            return connection if connected_after_attempt else None

        coordinator._ensure_connected.side_effect = connect
        stop = asyncio.create_task(coordinator.stop("box-1", 150, "TAG", "Local", authorize_stop=True))
        await asyncio.wait_for(entered.wait(), 1)
        assert not stop.done()
        assert cp.data.get.ocpp.rfid_stop is False
        assert cp.data.get.ocpp.pending_transactions == []
        connection.cp._authorize.assert_not_awaited()
        release.set()
        assert await asyncio.wait_for(stop, 1) is True
        assert cp.data.get.ocpp.rfid_stop is True
        if connected_after_attempt:
            connection.cp._authorize.assert_awaited_once_with(id_tag="TAG")
            connection.cp._stop_transaction.assert_awaited_once()
            assert cp.data.get.ocpp.pending_transactions == []
        else:
            connection.cp._authorize.assert_not_awaited()
            connection.cp._stop_transaction.assert_not_awaited()
            assert cp.data.get.ocpp.pending_transactions[0]["transaction_id"] == 42

    asyncio.run(check())


@pytest.mark.parametrize("disconnected", [False, True])
@pytest.mark.parametrize("auth_result", ["timeout", "Blocked", "Invalid", "missing_response"])
def test_same_tag_rfid_stop_only_falls_back_on_actual_disconnect(transaction_setup, disconnected, auth_result):
    coordinator, connection, cp = transaction_setup

    async def check():
        assert await coordinator.start("box-1", 1, "TAG", 100)
        connection.ws = SimpleNamespace(closed=False)

        async def authorize(**kwargs):
            connection.ws.closed = disconnected
            if auth_result == "timeout":
                raise asyncio.TimeoutError("no response")
            if auth_result == "missing_response":
                return None
            return SimpleNamespace(id_tag_info={"status": auth_result})

        connection.cp._authorize.reset_mock()
        connection.cp._authorize.side_effect = authorize
        expected = disconnected and auth_result in ("timeout", "missing_response")
        assert await coordinator.stop("box-1", 150, "TAG", "Local", authorize_stop=True) is expected
        connection.cp._authorize.assert_awaited_once_with(id_tag="TAG")
        connection.cp._stop_transaction.assert_not_awaited()
        assert cp.data.get.ocpp.rfid_stop is expected
        assert bool(cp.data.get.ocpp.pending_transactions) is expected
        if not expected:
            assert coordinator.get_state("box-1") == TransactionState.ACTIVE

    asyncio.run(check())


def test_different_tag_cannot_use_offline_rfid_stop_fallback(transaction_setup, mock_pub):
    coordinator, connection, cp = transaction_setup

    async def check():
        assert await coordinator.start("box-1", 1, "TAG", 100)
        coordinator._ensure_connected.return_value = None
        connection.cp._authorize.reset_mock()
        mock_pub.pub.reset_mock()
        assert await coordinator.stop("box-1", 150, "OTHER", "Local", authorize_stop=True) is False
        assert coordinator.get_state("box-1") == TransactionState.ACTIVE
        assert cp.data.get.ocpp.rfid_stop is False
        assert cp.data.get.ocpp.pending_transactions == []
        connection.cp._authorize.assert_not_awaited()
        connection.cp._stop_transaction.assert_not_awaited()
        mock_pub.pub.assert_not_called()

    asyncio.run(check())


@pytest.mark.parametrize("state", [
    TransactionState.IDLE, TransactionState.REJECTED, TransactionState.ERROR,
    TransactionState.START_PENDING, TransactionState.AUTHORIZING,
    TransactionState.STARTING, TransactionState.STOPPING,
])
def test_rfid_stop_requires_stoppable_transaction(transaction_setup, mock_pub, state):
    coordinator, connection, _ = transaction_setup
    transaction = coordinator._get_transaction("box-1")
    transaction.state = state

    assert asyncio.run(coordinator.stop("box-1", 150, "STOP_TAG", "Local", authorize_stop=True)) is False

    assert transaction.state == state
    assert transaction.pending_stop is None
    connection.cp._authorize.assert_not_awaited()
    connection.cp._stop_transaction.assert_not_awaited()
    mock_pub.pub.assert_not_called()


@pytest.mark.parametrize("restart", [False, True])
def test_automatic_stop_during_rfid_auth_does_not_stop_again(transaction_setup, restart):
    coordinator, connection, _ = transaction_setup

    async def check():
        assert await coordinator.start("box-1", 1, "START_TAG", 100)
        entered = asyncio.Event()
        release = asyncio.Event()

        async def delayed_authorize(**kwargs):
            entered.set()
            await release.wait()
            return SimpleNamespace(id_tag_info={"status": "Accepted"})

        connection.cp._authorize.side_effect = delayed_authorize
        rfid_stop = asyncio.create_task(coordinator.stop("box-1", 150, "STOP_TAG", "Local", authorize_stop=True))
        await asyncio.wait_for(entered.wait(), timeout=5)
        assert await coordinator.stop("box-1", 160, reason="EVDisconnected")
        if restart:
            connection.cp._authorize.side_effect = None
            connection.cp._start_transaction.return_value.transaction_id = 43
            assert await coordinator.start("box-1", 1, "NEW_TAG", 200)
        release.set()
        assert await rfid_stop is False

    asyncio.run(check())

    connection.cp._stop_transaction.assert_awaited_once_with(
        meter_stop=160, transaction_id=42, reason="EVDisconnected", id_tag="START_TAG",
        timestamp=ANY,
    )
    assert coordinator.get_transaction_id("box-1") == (43 if restart else None)


def test_parallel_rfid_stops_send_one_stop_transaction(transaction_setup):
    coordinator, connection, _ = transaction_setup

    async def check():
        assert await coordinator.start("box-1", 1, "START_TAG", 100)
        entered = asyncio.Event()
        release = asyncio.Event()

        async def delayed_stop(**kwargs):
            entered.set()
            await release.wait()
            return SimpleNamespace(id_tag_info=None)

        connection.cp._stop_transaction.side_effect = delayed_stop
        first = asyncio.create_task(coordinator.stop("box-1", 150, "TAG", "Local", authorize_stop=True))
        second = asyncio.create_task(coordinator.stop("box-1", 150, "TAG", "Local", authorize_stop=True))
        await asyncio.wait_for(entered.wait(), timeout=5)
        assert await second is False
        release.set()
        assert await first is True

    asyncio.run(check())

    connection.cp._stop_transaction.assert_awaited_once()


@pytest.mark.parametrize("reason", ["EVDisconnected", "Remote", "SoftReset"])
def test_automatic_stop_does_not_authorize(transaction_setup, reason):
    coordinator, connection, _ = transaction_setup

    async def check():
        assert await coordinator.start("box-1", 1, "TAG", 100)
        connection.cp._authorize.reset_mock()
        connection.cp._authorize.side_effect = RuntimeError("must not authorize")
        if reason == "SoftReset":
            assert await coordinator.stop_and_wait("box-1", 150, "TAG", reason)
        else:
            assert await coordinator.stop("box-1", 150, "TAG", reason)

    asyncio.run(check())

    connection.cp._authorize.assert_not_awaited()
    connection.cp._stop_transaction.assert_awaited_once()


def test_stop_and_wait_replays_persisted_stop_after_restart(transaction_setup):
    coordinator, connection, openwb_cp = transaction_setup

    async def check():
        assert await coordinator.start("box-1", 1, "TAG", 100)
        coordinator._ensure_connected.return_value = None
        assert await coordinator.stop("box-1", 150) is False
        assert openwb_cp.data.get.ocpp.transaction_id is None
        assert openwb_cp.data.get.ocpp.pending_transactions

        connect = AsyncMock(return_value=connection)
        restored = TransactionCoordinator(ensure_connected=connect)
        wait = asyncio.create_task(restored.stop_and_wait("box-1", 150, timeout=None))
        await asyncio.sleep(0)
        assert not wait.done()
        connect.assert_awaited_once_with("box-1")
        # Wie bei erfolgreicher Verbindungsinitialisierung den Replay ausführen.
        await restored.on_connected("box-1", connection)
        assert await asyncio.wait_for(wait, 1) is True
        assert openwb_cp.data.get.ocpp.pending_transactions == []

    asyncio.run(check())
    connection.cp._stop_transaction.assert_awaited_once()


@pytest.mark.parametrize("state", [TransactionState.START_UNCONFIRMED, TransactionState.ERROR])
def test_bounded_stop_and_wait_returns_on_unknown_start_error(transaction_setup, state):
    coordinator, _, _ = transaction_setup
    coordinator._get_transaction("box-1").state = state

    async def check():
        assert await asyncio.wait_for(coordinator.stop_and_wait("box-1", 150), 1) is False

    asyncio.run(check())


def test_bounded_stop_and_wait_does_not_report_pending_stop_as_completed(transaction_setup):
    coordinator, connection, openwb_cp = transaction_setup

    async def check():
        assert await coordinator.start("box-1", 1, "TAG", 100)
        coordinator._ensure_connected.return_value = None
        assert await coordinator.stop("box-1", 150) is False
        restored = TransactionCoordinator(ensure_connected=AsyncMock(return_value=None))
        assert await restored.stop_and_wait("box-1", 150, timeout=0.01) is False
        assert openwb_cp.data.get.ocpp.pending_transactions

    asyncio.run(check())
    connection.cp._stop_transaction.assert_not_awaited()


def test_active_stop_clears_transaction_only_after_response(transaction_setup):
    coordinator, connection, openwb_cp = transaction_setup

    async def check():
        entered = asyncio.Event()
        release = asyncio.Event()

        async def delayed_stop(**kwargs):
            entered.set()
            await release.wait()
            return SimpleNamespace(id_tag_info=None)

        connection.cp._stop_transaction.side_effect = delayed_stop
        await coordinator.start("box-1", 1, "TAG", 100)
        stop = asyncio.create_task(coordinator.stop("box-1", 150, "", "EVDisconnected"))
        await entered.wait()
        assert coordinator.get_state("box-1") == TransactionState.STOPPING
        assert openwb_cp.data.get.ocpp.transaction_id == 42
        assert await coordinator.stop("box-1", 150, "", "EVDisconnected") is False
        release.set()
        assert await stop is True

    asyncio.run(check())

    connection.cp._stop_transaction.assert_awaited_once()
    assert coordinator.get_state("box-1") == TransactionState.IDLE
    assert openwb_cp.data.get.ocpp.transaction_id is None
    assert openwb_cp.data.get.ocpp.tag_accepted is False


def test_missing_stop_confirmation_preserves_pending_stop(transaction_setup):
    coordinator, connection, openwb_cp = transaction_setup
    connection.cp._stop_transaction.return_value = None

    async def check():
        assert await coordinator.start("box-1", 1, "TAG", 100)
        assert await coordinator.stop("box-1", 150, "", "EVDisconnected") is False

    asyncio.run(check())

    assert coordinator.get_state("box-1") == TransactionState.ERROR
    assert coordinator.get_transaction_id("box-1") == 42
    assert openwb_cp.data.get.ocpp.pending_transactions == [{
        "action": "stop", "transaction_id": 42, "id_tag": "TAG",
        "imported": 150, "reason": "EVDisconnected", "timestamp": ANY,
    }]


def test_failed_stop_keeps_internal_transaction_id_and_releases_local_state(transaction_setup):
    coordinator, connection, openwb_cp = transaction_setup
    connection.cp._stop_transaction.side_effect = RuntimeError("response lost")

    async def check():
        await coordinator.start("box-1", 1, "TAG", 100)
        assert await coordinator.stop("box-1", 150, "", "EVDisconnected") is False

    asyncio.run(check())

    assert coordinator.get_state("box-1") == TransactionState.ERROR
    assert coordinator.get_transaction_id("box-1") == 42
    assert openwb_cp.data.get.ocpp.transaction_id is None
    assert openwb_cp.data.get.ocpp.tag_accepted is False
    assert openwb_cp.data.get.ocpp.pending_transactions == [{
        "action": "stop", "transaction_id": 42, "id_tag": "TAG",
        "imported": 150, "reason": "EVDisconnected", "timestamp": ANY,
    }]


@pytest.mark.parametrize("transaction_id", [42, 0, -123])
def test_offline_stop_is_replayed_once_after_reconnect(transaction_setup, mock_pub, transaction_id):
    coordinator, connection, openwb_cp = transaction_setup
    connection.cp._start_transaction.return_value.transaction_id = transaction_id

    async def check():
        await coordinator.start("box-1", 1, "TAG", 100)
        coordinator._ensure_connected.return_value = None
        assert await coordinator.stop("box-1", 150, "", "EVDisconnected") is False
        assert openwb_cp.data.get.ocpp.pending_transactions == [{
            "action": "stop", "transaction_id": transaction_id, "id_tag": "TAG",
            "imported": 150, "reason": "EVDisconnected", "timestamp": ANY,
        }]
        connection.cp._authorize.reset_mock()
        connection.cp._authorize.side_effect = RuntimeError("must not authorize replay")
        coordinator._ensure_connected.return_value = connection
        transaction_id_publications_before_replay = mock_pub.pub.call_args_list.count(
            call("openWB/set/chargepoint/1/get/ocpp/transaction_id", transaction_id)
        )
        await coordinator.on_connected("box-1", connection)
        await coordinator.on_connected("box-1", connection)
        return transaction_id_publications_before_replay

    transaction_id_publications_before_replay = asyncio.run(check())

    connection.cp._authorize.assert_not_awaited()
    connection.cp._stop_transaction.assert_awaited_once_with(
        meter_stop=150, transaction_id=transaction_id, reason="EVDisconnected", id_tag="TAG",
        timestamp=ANY,
    )
    assert openwb_cp.data.get.ocpp.pending_transactions == []
    assert coordinator.get_state("box-1") == TransactionState.IDLE
    assert mock_pub.pub.call_args_list.count(
        call("openWB/set/chargepoint/1/get/ocpp/pending_transactions", [])
    ) == 1
    assert mock_pub.pub.call_args_list.count(
        call("openWB/set/chargepoint/1/get/ocpp/transaction_id", transaction_id)
    ) == transaction_id_publications_before_replay


@pytest.mark.parametrize("transaction_id", [42, 0, -123])
def test_missing_stop_confirmation_does_not_delete_persisted_stop(transaction_setup, transaction_id):
    coordinator, connection, openwb_cp = transaction_setup
    connection.cp._start_transaction.return_value.transaction_id = transaction_id

    async def check():
        assert await coordinator.start("box-1", 1, "TAG", 100)
        coordinator._ensure_connected.return_value = None
        assert await coordinator.stop("box-1", 150, "", "EVDisconnected") is False
        coordinator._ensure_connected.return_value = connection
        connection.cp._stop_transaction.return_value = None
        await coordinator.on_connected("box-1", connection)

    asyncio.run(check())

    assert coordinator.get_state("box-1") == TransactionState.ERROR
    assert coordinator.get_transaction_id("box-1") == transaction_id
    assert len(openwb_cp.data.get.ocpp.pending_transactions) == 1
    assert openwb_cp.data.get.ocpp.pending_transactions[0]["transaction_id"] == transaction_id
    connection.cp._stop_transaction.assert_awaited_once_with(
        meter_stop=150, transaction_id=transaction_id, reason="EVDisconnected", id_tag="TAG", timestamp=ANY,
    )


def test_failed_offline_stop_replay_keeps_transaction_id_cleared(transaction_setup, mock_pub):
    coordinator, connection, openwb_cp = transaction_setup

    async def check():
        await coordinator.start("box-1", 1, "TAG", 100)
        coordinator._ensure_connected.return_value = None
        assert await coordinator.stop("box-1", 150, "", "EVDisconnected") is False
        transaction_id_publications_before_replay = mock_pub.pub.call_args_list.count(
            call("openWB/set/chargepoint/1/get/ocpp/transaction_id", 42)
        )

        coordinator._ensure_connected.return_value = connection
        connection.cp._stop_transaction.side_effect = RuntimeError("response lost")
        await coordinator.on_connected("box-1", connection)

        assert coordinator.get_state("box-1") == TransactionState.ERROR
        assert coordinator.get_transaction_id("box-1") == 42
        assert openwb_cp.data.get.ocpp.transaction_id is None
        assert openwb_cp.data.get.ocpp.tag_accepted is False
        assert openwb_cp.data.get.ocpp.pending_transactions
        assert mock_pub.pub.call_args_list.count(
            call("openWB/set/chargepoint/1/get/ocpp/transaction_id", 42)
        ) == transaction_id_publications_before_replay

    asyncio.run(check())


def test_stale_disconnect_does_not_cancel_new_connection_replay_task(transaction_setup):
    coordinator, connection, _ = transaction_setup

    async def check():
        old_connection = SimpleNamespace()
        retry_task = asyncio.create_task(asyncio.sleep(3600))
        coordinator._replay_tasks["box-1"] = retry_task
        coordinator._replay_task_connections["box-1"] = connection

        await coordinator.on_disconnected("box-1", old_connection)
        assert not retry_task.cancelled()
        assert coordinator._replay_tasks["box-1"] is retry_task

        await coordinator.on_disconnected("box-1", connection)
        assert retry_task.cancelled()
        assert "box-1" not in coordinator._replay_tasks

    asyncio.run(check())


def test_reconnect_replaces_old_replay_retry_task(transaction_setup, monkeypatch):
    coordinator, new_connection, _ = transaction_setup
    old_connection = SimpleNamespace()
    monkeypatch.setattr(ocpp_transaction_coordinator, "_get_config", lambda *args, **kwargs: 2)

    async def check():
        coordinator._schedule_replay_retry("box-1", old_connection)
        old_task = coordinator._replay_tasks["box-1"]

        coordinator._schedule_replay_retry("box-1", new_connection)
        new_task = coordinator._replay_tasks["box-1"]
        assert new_task is not old_task
        assert coordinator._replay_task_connections["box-1"] is new_connection

        await asyncio.sleep(0)
        assert old_task.cancelled()
        await coordinator.on_disconnected("box-1", old_connection)
        assert coordinator._replay_tasks["box-1"] is new_task
        assert not new_task.cancelled()

        await coordinator.on_disconnected("box-1", new_connection)
        assert new_task.cancelled()

    asyncio.run(check())


@pytest.fixture
def handler_setup(monkeypatch):
    openwb_cp = SimpleNamespace(
        num=1,
        data=SimpleNamespace(get=SimpleNamespace(ocpp=SimpleNamespace(
            transaction_id=None, availability=[True, True], pending_availability=[False, False],
            authorization_flow_status=None,
            config=ocpp_config_for_test(),
        ))),
    )
    monkeypatch.setattr(ocpp_chargepoint, "get_cp_from_chargebox_id", lambda _: openwb_cp)

    def make_charge_point():
        charge_point = OcppChargePoint("box-1", AsyncMock())
        charge_point.call = AsyncMock(return_value=SimpleNamespace())
        return charge_point

    return make_charge_point, openwb_cp


@pytest.mark.parametrize("connector_id", [0, 1])
@pytest.mark.parametrize("stage", ["active", "starting"])
def test_inoperative_availability_is_scheduled_until_stop(handler_setup, mock_pub, connector_id, stage):
    make_charge_point, openwb_cp = handler_setup
    if stage == "active":
        openwb_cp.data.get.ocpp.transaction_id = 42
    else:
        openwb_cp.data.get.ocpp.authorization_flow_status = "start_starting"

    async def check():
        charge_point = make_charge_point()
        result = await charge_point.on_change_availability(
            connector_id, AvailabilityType.inoperative,
        )
        assert result.status == AvailabilityStatus.scheduled
        assert openwb_cp.data.get.ocpp.availability == [True, True]
        assert openwb_cp.data.get.ocpp.pending_availability == [connector_id == 0, True]
        await charge_point.apply_pending_availability()
        assert openwb_cp.data.get.ocpp.availability == [True, True]
        openwb_cp.data.get.ocpp.transaction_id = None
        openwb_cp.data.get.ocpp.authorization_flow_status = None
        await charge_point.apply_pending_availability()

    asyncio.run(check())

    assert openwb_cp.data.get.ocpp.availability == [connector_id == 1, False]
    assert openwb_cp.data.get.ocpp.pending_availability == [False, False]
    mock_pub.pub.assert_any_call("openWB/set/chargepoint/1/get/ocpp/availability", [connector_id == 1, False])


@pytest.mark.parametrize("connector_id", [0, 1])
@pytest.mark.parametrize("outcome", ["accepted", "Blocked", "Expired", "Invalid", "ConcurrentTx",
                                   "timeout", "missing_response"])
def test_availability_during_start_is_applied_after_transaction_or_explicit_rejection(
        transaction_setup, monkeypatch, connector_id, outcome):
    coordinator, connection, openwb_cp = transaction_setup
    monkeypatch.setattr(ocpp_chargepoint, "get_cp_from_chargebox_id", lambda _: openwb_cp)

    async def check():
        handler = OcppChargePoint("box-1", AsyncMock())
        connection.cp.apply_pending_availability = AsyncMock(wraps=handler.apply_pending_availability)
        entered = asyncio.Event()
        release = asyncio.Event()

        async def delayed_start(**kwargs):
            entered.set()
            await release.wait()
            if outcome == "timeout":
                raise asyncio.TimeoutError("start response lost")
            if outcome == "missing_response":
                return None
            if outcome != "accepted":
                return SimpleNamespace(id_tag_info={"status": outcome}, transaction_id=42)
            return connection.cp._start_transaction.return_value

        connection.cp._start_transaction.side_effect = delayed_start
        start = asyncio.create_task(coordinator.start("box-1", 1, "TAG", 100))
        await asyncio.wait_for(entered.wait(), 5)
        assert coordinator.get_state("box-1") == TransactionState.STARTING
        assert openwb_cp.data.get.ocpp.transaction_id is None

        response = await handler.on_change_availability(connector_id, AvailabilityType.inoperative)
        assert response.status == AvailabilityStatus.scheduled
        assert openwb_cp.data.get.ocpp.availability == [True, True]
        assert openwb_cp.data.get.ocpp.pending_availability == [connector_id == 0, True]

        # Auch ein zusätzlicher Aufruf während der ausstehenden Startantwort
        # darf die Vormerkung nicht vorzeitig anwenden.
        await handler.apply_pending_availability()
        assert openwb_cp.data.get.ocpp.availability == [True, True]
        assert openwb_cp.data.get.ocpp.pending_availability == [connector_id == 0, True]

        release.set()
        result = await asyncio.wait_for(start, 5)
        connection.cp._stop_transaction.assert_not_awaited()
        if outcome == "accepted":
            assert result is True
            assert coordinator.get_state("box-1") == TransactionState.ACTIVE
            assert openwb_cp.data.get.ocpp.transaction_id == 42
            assert openwb_cp.data.get.ocpp.tag_accepted is True
            assert openwb_cp.data.get.ocpp.availability == [True, True]
            connection.cp.apply_pending_availability.assert_not_awaited()
            assert await coordinator.stop("box-1", 150, reason="Local") is True
            connection.cp._stop_transaction.assert_awaited_once()
            connection.cp.apply_pending_availability.assert_awaited_once()
            assert coordinator.get_state("box-1") == TransactionState.IDLE
        elif outcome in ("timeout", "missing_response"):
            assert result is False
            assert coordinator.get_state("box-1") == TransactionState.START_UNCONFIRMED
            assert openwb_cp.data.get.ocpp.availability == [True, True]
            assert openwb_cp.data.get.ocpp.pending_availability == [connector_id == 0, True]
            connection.cp.apply_pending_availability.assert_not_awaited()
            await handler.apply_pending_availability()
            assert openwb_cp.data.get.ocpp.availability == [True, True]

            openwb_cp.data.get.plug_state = False
            client = object.__new__(OcppClient)
            client.transactions = coordinator
            client.connection_manager = SimpleNamespace(get=lambda _: connection)
            await client._clear_start_block("box-1")
            assert coordinator.get_state("box-1") == TransactionState.IDLE
            connection.cp.apply_pending_availability.assert_awaited_once()
        else:
            assert result is False
            assert coordinator.get_state("box-1") == TransactionState.REJECTED
            connection.cp.apply_pending_availability.assert_awaited_once()

        assert openwb_cp.data.get.ocpp.transaction_id is None
        assert openwb_cp.data.get.ocpp.tag_accepted is False
        assert openwb_cp.data.get.ocpp.availability == [connector_id == 1, False]
        assert openwb_cp.data.get.ocpp.pending_availability == [False, False]

    asyncio.run(check())


@pytest.mark.parametrize("waiting_for", ["connect", "authorize"])
@pytest.mark.parametrize("connector_id", [0, 1])
def test_inoperative_before_start_request_is_immediate_and_prevents_start(
        transaction_setup, monkeypatch, waiting_for, connector_id):
    coordinator, connection, openwb_cp = transaction_setup
    monkeypatch.setattr(ocpp_chargepoint, "get_cp_from_chargebox_id", lambda _: openwb_cp)

    async def check():
        handler = OcppChargePoint("box-1", AsyncMock())
        entered = asyncio.Event()
        release = asyncio.Event()
        waiting = coordinator._ensure_connected if waiting_for == "connect" else connection.cp._authorize

        async def delayed(*args, **kwargs):
            entered.set()
            await release.wait()
            return waiting.return_value

        waiting.side_effect = delayed
        start = asyncio.create_task(coordinator.start("box-1", 1, "TAG", 100))
        await asyncio.wait_for(entered.wait(), 5)
        response = await handler.on_change_availability(connector_id, AvailabilityType.inoperative)
        assert response.status == AvailabilityStatus.accepted
        assert openwb_cp.data.get.ocpp.availability == [connector_id == 1, False]
        assert openwb_cp.data.get.ocpp.pending_availability == [False, False]
        release.set()
        assert await asyncio.wait_for(start, 5) is False

    asyncio.run(check())
    connection.cp._start_transaction.assert_not_awaited()
    connection.cp._stop_transaction.assert_not_awaited()
    assert coordinator.get_state("box-1") == TransactionState.IDLE


def test_change_availability_rejects_unknown_connector(handler_setup):
    make_charge_point, openwb_cp = handler_setup

    async def check():
        charge_point = make_charge_point()
        return await charge_point.on_change_availability(2, AvailabilityType.inoperative)

    result = asyncio.run(check())

    assert result.status == AvailabilityStatus.rejected
    assert openwb_cp.data.get.ocpp.availability == [True, True]


def test_immediate_availability_change_clears_pending_request(handler_setup, mock_pub):
    make_charge_point, openwb_cp = handler_setup
    openwb_cp.data.get.ocpp.pending_availability = [False, True]

    async def check():
        charge_point = make_charge_point()
        return await charge_point.on_change_availability(1, AvailabilityType.inoperative)

    response = asyncio.run(check())

    assert response.status == AvailabilityStatus.accepted
    assert openwb_cp.data.get.ocpp.availability == [True, False]
    assert openwb_cp.data.get.ocpp.pending_availability == [False, False]
    mock_pub.pub.assert_any_call(
        "openWB/set/chargepoint/1/get/ocpp/pending_availability",
        [False, False],
    )


def test_availability_defaults_are_independent():
    first, second = Ocpp(), Ocpp()
    first.availability[0] = False
    first.pending_availability[1] = True
    assert second.availability == [True, True]
    assert second.pending_availability == [False, False]


@pytest.mark.parametrize("field_name", ["availability", "pending_availability"])
@pytest.mark.parametrize("payload,expected", [
    ([True, False], [True, False]),
    ([False, True], [False, True]),
])
def test_availability_mqtt_roundtrip(mock_pub, field_name, payload, expected):
    set_handler = SetData(Event(), Event(), Event(), Event())
    topic = f"openWB/chargepoint/1/get/ocpp/{field_name}"
    set_message = SimpleNamespace(topic=topic.replace("openWB/", "openWB/set/", 1),
                                  payload=json.dumps(payload).encode())
    set_handler.process_chargepoint_get_topics(set_message)
    mock_pub.pub.assert_any_call(topic, expected, retain=True)
    mock_pub.pub.assert_any_call(set_message.topic, "")

    subscriber = object.__new__(SubData)
    ocpp_state = Ocpp()
    chargepoints = {"cp1": SimpleNamespace(chargepoint=SimpleNamespace(
        data=SimpleNamespace(get=SimpleNamespace(ocpp=ocpp_state))))}
    mock_pub.pub.reset_mock()
    subscriber.process_chargepoint_topic(
        chargepoints, SimpleNamespace(topic=topic, payload=json.dumps(payload).encode()))
    assert getattr(ocpp_state, field_name) == expected
    mock_pub.pub.assert_not_called()
    subscriber.process_chargepoint_topic(
        chargepoints, SimpleNamespace(topic=topic, payload=json.dumps(expected).encode()))
    assert getattr(ocpp_state, field_name) == expected


@pytest.mark.parametrize("field_name", ["availability", "pending_availability"])
@pytest.mark.parametrize("payload", [[], [True], [True, False, True], [True, 0], [1, False],
                                     [True, "false"], None, {}, "false", 1, True, False])
def test_availability_mqtt_rejects_invalid_arrays(mock_pub, field_name, payload):
    set_handler = SetData(Event(), Event(), Event(), Event())
    topic = f"openWB/chargepoint/1/get/ocpp/{field_name}"
    set_message = SimpleNamespace(topic=topic.replace("openWB/", "openWB/set/", 1),
                                  payload=json.dumps(payload).encode())
    set_handler.process_chargepoint_get_topics(set_message)
    mock_pub.pub.assert_called_once_with(set_message.topic, "")


@pytest.mark.parametrize("connector_id,availability_type,initial,expected", [
    (0, AvailabilityType.inoperative, [True, True], [False, False]),
    (1, AvailabilityType.inoperative, [True, True], [True, False]),
    (1, AvailabilityType.operative, [False, False], [False, True]),
    (0, AvailabilityType.operative, [False, False], [True, True]),
])
def test_availability_changes_target_connectors(handler_setup, connector_id, availability_type, initial, expected):
    make_charge_point, openwb_cp = handler_setup
    openwb_cp.data.get.ocpp.availability = initial

    async def check():
        return await make_charge_point().on_change_availability(connector_id, availability_type)

    response = asyncio.run(check())
    assert response.status == AvailabilityStatus.accepted
    assert openwb_cp.data.get.ocpp.availability == expected
    assert initial in ([True, True], [False, False])


def test_availability_operative_clears_only_targeted_pending_entries(handler_setup, mock_pub):
    make_charge_point, openwb_cp = handler_setup
    openwb_cp.data.get.ocpp.transaction_id = 42

    async def check():
        charge_point = make_charge_point()
        await charge_point.on_change_availability(0, AvailabilityType.inoperative)
        await charge_point.on_change_availability(1, AvailabilityType.operative)
        assert openwb_cp.data.get.ocpp.pending_availability == [True, False]
        openwb_cp.data.get.ocpp.transaction_id = None
        await charge_point.apply_pending_availability()

    asyncio.run(check())
    assert openwb_cp.data.get.ocpp.availability == [False, True]
    assert openwb_cp.data.get.ocpp.pending_availability == [False, False]
    mock_pub.pub.assert_any_call("openWB/set/chargepoint/1/get/ocpp/pending_availability", [True, True])


@pytest.mark.parametrize("availability,expected_status", [
    ([True, True], RemoteStartStopStatus.accepted),
    ([True, False], RemoteStartStopStatus.rejected),
    ([False, True], RemoteStartStopStatus.rejected),
    ([False, False], RemoteStartStopStatus.rejected),
])
def test_remote_start_checks_both_connector_availabilities(handler_setup, monkeypatch, availability, expected_status):
    make_charge_point, openwb_cp = handler_setup
    openwb_cp.data.get.ocpp.availability = availability
    openwb_cp.template = SimpleNamespace(data=SimpleNamespace(valid_tags=["TAG"]))
    monkeypatch.setattr(data, "data", SimpleNamespace(
        optional_data=SimpleNamespace(data=SimpleNamespace(rfid=SimpleNamespace(active=True))),
        ev_data={},
    ))

    async def check():
        return await make_charge_point().remote_start_transaction("TAG", 1)

    assert asyncio.run(check()).status == expected_status


@pytest.mark.parametrize("rfid_active,template_tags,vehicle_tags,expected_status", [
    (True, ["TAG"], [], RemoteStartStopStatus.accepted),
    (True, [], ["OTHER", "TAG"], RemoteStartStopStatus.accepted),
    (True, [], [], RemoteStartStopStatus.rejected),
    (True, ["OTHER"], ["OTHER"], RemoteStartStopStatus.rejected),
    (False, ["TAG"], ["TAG"], RemoteStartStopStatus.rejected),
    (False, [], [], RemoteStartStopStatus.rejected),
    (True, None, ["TAG"], RemoteStartStopStatus.rejected),
])
def test_remote_start_requires_local_rfid_permission(
        handler_setup, monkeypatch, mock_pub, caplog,
        rfid_active, template_tags, vehicle_tags, expected_status):
    make_charge_point, openwb_cp = handler_setup
    openwb_cp.template = (SimpleNamespace(data=SimpleNamespace(valid_tags=template_tags))
                          if template_tags is not None else None)
    monkeypatch.setattr(data, "data", SimpleNamespace(
        optional_data=SimpleNamespace(data=SimpleNamespace(rfid=SimpleNamespace(active=rfid_active))),
        ev_data={"ev1": SimpleNamespace(data=SimpleNamespace(tag_id=vehicle_tags))},
    ))

    async def check():
        return await make_charge_point().remote_start_transaction("TAG", 1)

    with caplog.at_level("INFO", logger=ocpp_chargepoint.__name__):
        assert asyncio.run(check()).status == expected_status

    if expected_status == RemoteStartStopStatus.accepted:
        mock_pub.pub.assert_called_once_with("openWB/set/chargepoint/1/get/rfid", "TAG")
    else:
        mock_pub.pub.assert_not_called()
        assert "Remote-Start abgelehnt" in caplog.text


@pytest.mark.parametrize("stop_flag", ["remote_stop", "rfid_stop", "reset", "unlock_stop"])
def test_remote_start_rejects_stop_flags_without_forwarding_tag(handler_setup, mock_pub, monkeypatch, stop_flag):
    make_charge_point, cp = handler_setup
    cp.template = SimpleNamespace(data=SimpleNamespace(valid_tags=["TAG"]))
    setattr(cp.data.get.ocpp, stop_flag, True)
    monkeypatch.setattr(data, "data", SimpleNamespace(
        optional_data=SimpleNamespace(data=SimpleNamespace(rfid=SimpleNamespace(active=True))),
        ev_data={},
    ))

    async def check():
        response = await make_charge_point().remote_start_transaction("TAG", 1)
        assert response.status == RemoteStartStopStatus.rejected

    asyncio.run(check())
    mock_pub.pub.assert_not_called()


@pytest.fixture
def connection_config_setup(handler_setup, monkeypatch):
    _, openwb_cp = handler_setup
    openwb_cp.data.get.ocpp.test_reconnect = False
    openwb_cp.data.config = SimpleNamespace(ocpp_chargebox_password="secret")
    config = SimpleNamespace(active=True, url="wss://old.example/ocpp/", version="ocpp1.6")
    monkeypatch.setattr(data, "data", SimpleNamespace(
        optional_data=SimpleNamespace(data=SimpleNamespace(ocpp=SimpleNamespace(config=config))),
        cp_data={"cp1": openwb_cp},
    ))
    monkeypatch.setattr(ocpp_connection_manager, "get_cp_from_chargebox_id", lambda _: openwb_cp)
    manager = OcppConnectionManager(
        chargepoint_factory=lambda *_: SimpleNamespace(),
        on_connected=AsyncMock(return_value=True),
        on_disconnected=AsyncMock(),
    )
    old = SimpleNamespace(
        server_url="wss://old.example/ocpp", subprotocol="ocpp1.6", closing=False,
        start_task=SimpleNamespace(done=lambda: False), ws=SimpleNamespace(closed=False),
    )
    manager._connections["box-1"] = old
    manager._last_connection_settings["box-1"] = (old.server_url, old.subprotocol)
    return manager, old, config, openwb_cp


@pytest.fixture
def identity_change_setup(monkeypatch):
    cp = SimpleNamespace(num=1, data=SimpleNamespace(
        config=SimpleNamespace(ocpp_chargebox_id="NEW", ocpp_chargebox_password="pw"),
        get=SimpleNamespace(imported=150, plug_state=True, ocpp=Ocpp(
            previous_chargebox_id="OLD", transaction_id=42, transaction_id_tag="TAG",
        )),
    ))
    monkeypatch.setattr(data, "data", SimpleNamespace(
        cp_data={"cp1": cp},
        optional_data=SimpleNamespace(data=SimpleNamespace(ocpp=SimpleNamespace(
            config=SimpleNamespace(active=True),
        ))),
    ))
    connection = SimpleNamespace(boot_accepted=True, cp=SimpleNamespace(
        openwb_cp=cp, _stop_transaction=AsyncMock(return_value=SimpleNamespace()),
        _authorize=AsyncMock(return_value=SimpleNamespace(id_tag_info={"status": "Accepted"})),
        _start_transaction=AsyncMock(return_value=SimpleNamespace(
            id_tag_info={"status": "Accepted"}, transaction_id=43,
        )),
        apply_pending_availability=AsyncMock(),
    ))
    client = object.__new__(OcppClient)
    client._identity_change_jobs = {}
    client._chargepoint_lifecycle = {}
    client._meter_snapshots = {"OLD": SimpleNamespace()}
    client._rfid_authorize_pending = {}
    client.connection_manager = SimpleNamespace(
        connect=AsyncMock(return_value=connection), disconnect=AsyncMock(),
    )
    client.transactions = TransactionCoordinator(
        ensure_connected=client.connection_manager.connect,
    )
    return client, cp, connection


def test_id_change_stops_old_transaction_before_connecting_new_identity(identity_change_setup, mock_pub):
    client, cp, connection = identity_change_setup
    events = []

    async def stop(**kwargs):
        assert get_cp_from_chargebox_id("OLD") is cp
        assert get_cp_from_chargebox_id("NEW") is None
        assert get_chargebox_id(cp) == "OLD"
        events.append(("stop", kwargs["transaction_id"]))
        return SimpleNamespace()

    async def disconnect(chargebox_id):
        assert cp.data.get.ocpp.transaction_id is None
        assert cp.data.get.ocpp.previous_chargebox_id == "OLD"
        events.append(("disconnect", chargebox_id))

    async def connect(chargebox_id):
        if chargebox_id == "NEW":
            assert cp.data.get.ocpp.transaction_id is None
            assert get_chargebox_id(cp) == "NEW"
            assert get_cp_from_chargebox_id("OLD") is None
            events.append(("connect", chargebox_id))
        return connection

    connection.cp._stop_transaction.side_effect = stop
    client.connection_manager.connect.side_effect = connect
    client.connection_manager.disconnect.side_effect = disconnect
    asyncio.run(client._change_chargebox_id(1, "OLD"))

    assert events == [("stop", 42), ("disconnect", "OLD"), ("connect", "NEW")]
    assert connection.cp._stop_transaction.await_args.kwargs["reason"] == "Other"
    assert connection.cp._stop_transaction.await_args.kwargs["meter_stop"] == 150
    assert "OLD" not in client._meter_snapshots
    mock_pub.pub.assert_any_call("openWB/set/chargepoint/1/get/ocpp/previous_chargebox_id", None)


@pytest.mark.parametrize("restored", [False, True])
def test_pending_id_change_survives_model_replacement_and_deduplicates_jobs(identity_change_setup, restored):
    client, cp, _ = identity_change_setup
    if not restored:
        cp.data.get.ocpp.previous_chargebox_id = None
        client._chargepoint_lifecycle[1] = ("OLD", "pw", True)
    submitted = []
    running = SimpleNamespace(done=lambda: False)

    def submit(coroutine, *args, **kwargs):
        coroutine.close()
        submitted.append(kwargs["chargebox_id"])
        return running

    client._submit = submit
    client.sync_chargepoint_lifecycle(1, "NEW", "pw", True)
    replacement = copy.deepcopy(cp)
    data.data.cp_data["cp1"] = replacement
    assert get_cp_from_chargebox_id("OLD") is replacement
    assert get_cp_from_chargebox_id("NEW") is None
    client.sync_chargepoint_lifecycle(1, "NEW", "pw", True)
    assert submitted == ["OLD"]
    assert replacement.data.get.ocpp.previous_chargebox_id == "OLD"


@pytest.mark.parametrize("new_id,active", [("NEW", True), ("NEW", False), (None, True)])
def test_id_change_without_transaction_only_reconnects_when_enabled(identity_change_setup, new_id, active):
    client, cp, connection = identity_change_setup
    cp.data.get.ocpp.transaction_id = None
    cp.data.get.ocpp.authorization_flow_status = "init"
    cp.data.config.ocpp_chargebox_id = new_id
    data.data.optional_data.data.ocpp.config.active = active

    asyncio.run(client._change_chargebox_id(1, "OLD"))

    connection.cp._stop_transaction.assert_not_awaited()
    client.connection_manager.disconnect.assert_awaited_once_with("OLD")
    assert cp.data.get.ocpp.previous_chargebox_id is None
    assert cp.data.get.ocpp.authorization_flow_status is None
    if new_id and active:
        client.connection_manager.connect.assert_awaited_once_with(new_id)
    else:
        client.connection_manager.connect.assert_not_awaited()


@pytest.mark.parametrize("flow_status", ["start_starting", "start_unconfirmed"])
def test_id_change_waits_for_unplug_when_start_is_unknown(identity_change_setup, flow_status):
    client, cp, _ = identity_change_setup
    cp.data.get.ocpp.transaction_id = None
    cp.data.get.ocpp.authorization_flow_status = flow_status

    async def check():
        change = asyncio.create_task(client._change_chargebox_id(1, "OLD"))
        await asyncio.sleep(0)
        assert not change.done()
        client.connection_manager.disconnect.assert_not_awaited()
        client.connection_manager.connect.assert_not_awaited()
        assert get_chargebox_id(cp) == "OLD"
        cp.data.get.plug_state = False
        client.transactions.clear_start_block("OLD")
        await asyncio.wait_for(change, 3)

    asyncio.run(check())
    client.connection_manager.disconnect.assert_awaited_once_with("OLD")
    client.connection_manager.connect.assert_awaited_once_with("NEW")


def test_id_change_does_not_connect_new_identity_without_stop_confirmation(identity_change_setup):
    client, cp, connection = identity_change_setup
    connection.cp._stop_transaction.side_effect = asyncio.TimeoutError()

    async def check():
        change = asyncio.create_task(client._change_chargebox_id(1, "OLD"))
        await asyncio.sleep(0)
        await asyncio.sleep(0)
        assert not change.done()
        assert cp.data.get.ocpp.previous_chargebox_id == "OLD"
        assert client.transactions.get_transaction_id("OLD") == 42
        assert cp.data.get.ocpp.pending_transactions[0]["transaction_id"] == 42
        client.connection_manager.disconnect.assert_not_awaited()
        assert all(call.args == ("OLD",) for call in client.connection_manager.connect.await_args_list)
        change.cancel()
        with pytest.raises(asyncio.CancelledError):
            await change

    asyncio.run(check())


@pytest.mark.parametrize("waiting_for", ["authorize", "start"])
def test_id_change_during_start_finishes_old_request_before_switch(identity_change_setup, waiting_for):
    client, cp, connection = identity_change_setup
    cp.data.config.ocpp_chargebox_id = "OLD"
    cp.data.get.ocpp.previous_chargebox_id = None
    cp.data.get.ocpp.transaction_id = None
    waiting = getattr(connection.cp, "_authorize" if waiting_for == "authorize" else "_start_transaction")

    async def check():
        entered = asyncio.Event()
        release = asyncio.Event()

        async def delayed(**kwargs):
            entered.set()
            await release.wait()
            return waiting.return_value

        waiting.side_effect = delayed
        start = asyncio.create_task(client.transactions.start("OLD", 1, "TAG", 100))
        await asyncio.wait_for(entered.wait(), 3)
        cp.data.config.ocpp_chargebox_id = "NEW"
        cp.data.get.ocpp.previous_chargebox_id = "OLD"
        change = asyncio.create_task(client._change_chargebox_id(1, "OLD"))
        await asyncio.sleep(0)
        client.connection_manager.disconnect.assert_not_awaited()
        assert await client.transactions.start("OLD", 1, "OTHER", 100) is False
        release.set()
        assert await asyncio.wait_for(start, 3) is False
        await asyncio.wait_for(change, 3)

    asyncio.run(check())
    if waiting_for == "authorize":
        connection.cp._start_transaction.assert_not_awaited()
        connection.cp._stop_transaction.assert_not_awaited()
    else:
        connection.cp._stop_transaction.assert_awaited_once()
        assert connection.cp._stop_transaction.await_args.kwargs["transaction_id"] == 43
        assert connection.cp._stop_transaction.await_args.kwargs["reason"] == "Other"
    client.connection_manager.disconnect.assert_awaited_once_with("OLD")
    assert client.connection_manager.connect.await_args_list[-1].args == ("NEW",)


def test_id_change_waits_for_offline_stop_replay(identity_change_setup):
    client, cp, connection = identity_change_setup
    client.connection_manager.connect.return_value = None

    async def check():
        change = asyncio.create_task(client._change_chargebox_id(1, "OLD"))
        await asyncio.sleep(0)
        assert cp.data.get.ocpp.pending_transactions[0]["transaction_id"] == 42
        assert not change.done()
        assert get_cp_from_chargebox_id("NEW") is None
        replacement = copy.deepcopy(cp)
        data.data.cp_data["cp1"] = replacement
        connection.cp.openwb_cp = replacement
        client.connection_manager.connect.return_value = connection
        await client.transactions.on_connected("OLD", connection)
        await asyncio.wait_for(change, 3)
        assert replacement.data.get.ocpp.pending_transactions == []
        assert replacement.data.get.ocpp.transaction_id is None
        assert replacement.data.get.ocpp.previous_chargebox_id is None

    asyncio.run(check())
    connection.cp._stop_transaction.assert_awaited_once()
    client.connection_manager.disconnect.assert_awaited_once_with("OLD")
    assert client.connection_manager.connect.await_args_list[-1].args == ("NEW",)


@pytest.mark.parametrize("old_id", ["OLD", None])
def test_id_change_retains_old_identity_in_mqtt_model(mock_pub, old_id):
    message = SimpleNamespace(
        topic="openWB/set/chargepoint/1/get/ocpp/previous_chargebox_id",
        payload=json.dumps(old_id).encode(),
    )
    SetData(Event(), Event(), Event(), Event()).process_chargepoint_get_topics(message)
    topic = message.topic.replace("openWB/set/", "openWB/", 1)
    mock_pub.pub.assert_any_call(topic, old_id, retain=True)
    model = Ocpp()
    subscriber = object.__new__(SubData)
    chargepoints = {"cp1": SimpleNamespace(chargepoint=SimpleNamespace(
        data=SimpleNamespace(get=SimpleNamespace(ocpp=model))))}
    subscriber.process_chargepoint_topic(chargepoints, SimpleNamespace(topic=topic, payload=json.dumps(old_id).encode()))
    assert asdict(model)["previous_chargebox_id"] == old_id


@pytest.mark.parametrize("change", ["none", "trailing_slash", "url", "version"])
def test_connection_reused_only_with_matching_config(connection_config_setup, change):
    manager, old, config, _ = connection_config_setup
    if change == "trailing_slash":
        config.url = config.url.rstrip("/")
    elif change == "url":
        config.url = "wss://new.example/ocpp"
    elif change == "version":
        config.version = "different-subprotocol"
    manager._cleanup_connection = AsyncMock()
    manager._open_connection = AsyncMock(return_value="new connection")

    assert manager.needs_configuration_refresh("box-1") == (change in ("url", "version"))
    result = asyncio.run(manager.ensure_connected("box-1"))

    if change in ("none", "trailing_slash"):
        assert result is old
        manager._cleanup_connection.assert_not_awaited()
        manager._open_connection.assert_not_awaited()
    else:
        assert result == "new connection"
        manager._cleanup_connection.assert_awaited_once_with(old)
        manager._open_connection.assert_awaited_once_with("box-1")


@pytest.mark.parametrize("stage", [
    "active", "init", "start_pending", "start_authorizing", "start_starting", "start_unconfirmed", "offline_stop",
])
def test_connection_config_change_waits_for_completion(connection_config_setup, caplog, stage):
    manager, old, config, openwb_cp = connection_config_setup
    config.url = "wss://new.example/ocpp"
    ocpp = openwb_cp.data.get.ocpp
    if stage == "active":
        ocpp.transaction_id = 42
    elif stage == "offline_stop":
        ocpp.pending_transactions = [{"transaction_id": 42}]
    else:
        ocpp.authorization_flow_status = stage
    manager._cleanup_connection = AsyncMock()
    manager._open_connection = AsyncMock(return_value="new connection")

    async def check():
        assert manager.needs_configuration_refresh("box-1") is False
        assert await manager.ensure_connected("box-1") is old
        assert await manager.ensure_connected("box-1") is old
        manager._cleanup_connection.assert_not_awaited()
        manager._open_connection.assert_not_awaited()
        assert caplog.text.count("Änderung von Server-URL oder Subprotocol zurückgestellt") == 1
        ocpp.transaction_id = None
        ocpp.authorization_flow_status = None
        ocpp.pending_transactions = []
        assert manager.needs_configuration_refresh("box-1") is True
        assert await manager.ensure_connected("box-1") == "new connection"

    asyncio.run(check())
    manager._cleanup_connection.assert_awaited_once_with(old)
    manager._open_connection.assert_awaited_once_with("box-1")


@pytest.mark.parametrize("busy", [False, True])
def test_reconnect_uses_pinned_config_until_transaction_completed(connection_config_setup, monkeypatch, busy):
    manager, old, config, openwb_cp = connection_config_setup
    manager._connections.clear()  # Transportverlust darf die Serverbindung nicht verlieren.
    config.url = "wss://new.example/ocpp"
    config.version = "new-subprotocol"
    openwb_cp.data.get.ocpp.transaction_id = 42 if busy else None
    expected_url = old.server_url if busy else config.url
    expected_version = old.subprotocol if busy else config.version
    ws = SimpleNamespace(subprotocol=expected_version, closed=False)
    connect = AsyncMock(return_value=ws)
    monkeypatch.setattr(ocpp_connection_manager.websockets, "connect", connect)
    manager._run_charge_point = AsyncMock()

    async def check():
        connection = await manager.ensure_connected("box-1")
        assert connection.server_url == expected_url
        assert connection.subprotocol == expected_version
        assert manager._last_connection_settings["box-1"] == (expected_url, expected_version)
        connect.assert_awaited_once_with(
            expected_url + "/box-1", subprotocols=[expected_version],
            extra_headers=manager.build_custom_headers("box-1", "secret"),
        )
        await connection.start_task

    asyncio.run(check())


def test_pending_availability_without_request_is_not_applied(handler_setup, mock_pub):
    make_charge_point, openwb_cp = handler_setup

    async def check():
        await make_charge_point().apply_pending_availability()

    asyncio.run(check())
    assert openwb_cp.data.get.ocpp.availability == [True, True]
    mock_pub.pub.assert_not_called()


@pytest.mark.parametrize("value", ["0", "-1", "not-a-number", "1.5"])
def test_invalid_configuration_interval_is_rejected(handler_setup, value):
    make_charge_point, _ = handler_setup

    async def check():
        charge_point = make_charge_point()
        response = await charge_point.change_configuration("HeartbeatInterval", value)
        assert charge_point.openwb_cp.data.get.ocpp.config.HeartbeatInterval["value"] == 10
        return response

    response = asyncio.run(check())

    assert response.status == ConfigurationStatus.rejected


def test_get_configuration_reads_dataclass_values(handler_setup):
    make_charge_point, _ = handler_setup

    async def check():
        charge_point = make_charge_point()
        response = await charge_point.get_configuration("HeartbeatInterval")
        return response

    response = asyncio.run(check())

    assert response.configuration_key[0] == {
        "key": "HeartbeatInterval",
        "value": "10",
        "readonly": False,
    }
    assert response.unknown_key == []


def test_get_config_supports_strings_and_preserves_integer_minimum():
    openwb_cp = SimpleNamespace(data=SimpleNamespace(get=SimpleNamespace(ocpp=SimpleNamespace(
        config=SimpleNamespace(
            TextSetting={"value": "hello"},
            IntSetting={"value": "0"},
        ),
    ))))

    assert _get_config(openwb_cp, "TextSetting", "fallback") == "hello"
    assert _get_config(openwb_cp, "IntSetting", 10) == 1
    assert _get_config(openwb_cp, "MissingSetting", "fallback") == "fallback"


def test_change_configuration_rejects_readonly_parameter(handler_setup):
    make_charge_point, openwb_cp = handler_setup
    openwb_cp.data.get.ocpp.config.HeartbeatInterval["readonly"] = True

    async def check():
        charge_point = make_charge_point()
        return await charge_point.change_configuration("HeartbeatInterval", "30")

    response = asyncio.run(check())

    assert response.status == ConfigurationStatus.rejected
    assert openwb_cp.data.get.ocpp.config.HeartbeatInterval["value"] == 10


@pytest.mark.parametrize(
    ("key", "initial_value", "new_value", "expected_value"),
    [
        ("TextSetting", "old", "new value", "new value"),
        ("EnabledSetting", False, "true", True),
        ("ScaleSetting", 1.5, "2.75", 2.75),
    ],
)
def test_change_configuration_uses_existing_field_type(
        handler_setup, key, initial_value, new_value, expected_value):
    make_charge_point, openwb_cp = handler_setup
    getattr(openwb_cp.data.get.ocpp.config, key)["value"] = initial_value

    async def check():
        charge_point = make_charge_point()
        return await charge_point.change_configuration(key, new_value)

    response = asyncio.run(check())

    assert response.status == ConfigurationStatus.accepted
    assert getattr(openwb_cp.data.get.ocpp.config, key)["value"] == expected_value


@pytest.mark.parametrize(
    ("key", "initial_value", "new_value"),
    [("EnabledSetting", False, "yes"), ("ScaleSetting", 1.5, "nan")],
)
def test_change_configuration_rejects_invalid_typed_values(
        handler_setup, key, initial_value, new_value):
    make_charge_point, openwb_cp = handler_setup
    getattr(openwb_cp.data.get.ocpp.config, key)["value"] = initial_value

    async def check():
        charge_point = make_charge_point()
        return await charge_point.change_configuration(key, new_value)

    response = asyncio.run(check())

    assert response.status == ConfigurationStatus.rejected
    assert getattr(openwb_cp.data.get.ocpp.config, key)["value"] == initial_value


@pytest.mark.parametrize("interval", [0, 30])
def test_valid_configuration_interval_is_used(handler_setup, interval):
    make_charge_point, _ = handler_setup

    async def check():
        charge_point = make_charge_point()
        response = await charge_point.change_configuration("MeterValueSampleInterval", str(interval))
        assert charge_point.openwb_cp.data.get.ocpp.config.MeterValueSampleInterval["value"] == interval
        return response

    response = asyncio.run(check())

    assert response.status == ConfigurationStatus.accepted


@pytest.mark.parametrize("value", ["-1", "not-a-number", "1.5"])
def test_invalid_meter_sample_interval_is_rejected(handler_setup, mock_pub, value):
    make_charge_point, cp = handler_setup
    original = cp.data.get.ocpp.config.MeterValueSampleInterval["value"]

    async def check():
        response = await make_charge_point().change_configuration("MeterValueSampleInterval", value)
        assert response.status == ConfigurationStatus.rejected

    asyncio.run(check())
    assert cp.data.get.ocpp.config.MeterValueSampleInterval["value"] == original
    mock_pub.pub.assert_not_called()


def test_set_configuration_value_publishes_parameter_dictionary(handler_setup, mock_pub):
    make_charge_point, openwb_cp = handler_setup

    async def check():
        charge_point = make_charge_point()
        await charge_point.set_configuration_value("MeterValueSampleInterval", 42)

    asyncio.run(check())

    assert openwb_cp.data.get.ocpp.config.MeterValueSampleInterval["value"] == 42
    mock_pub.pub.assert_called_once_with(
        "openWB/set/chargepoint/1/get/ocpp/config",
        asdict(openwb_cp.data.get.ocpp.config),
    )


def test_status_notification_sends_each_requested_message(handler_setup):
    make_charge_point, _ = handler_setup

    async def check():
        charge_point = make_charge_point()
        for force in (False, False, True):
            await charge_point._status_notification(
                connector_id=1, fault_state=0, fault_state_str="x" * 60,
                status=ChargePointStatus.available, force=force,
            )
        return charge_point

    charge_point = asyncio.run(check())

    assert charge_point.call.await_count == 3
    assert all(request.connector_id == 1 for request in (
        awaited.args[0] for awaited in charge_point.call.await_args_list
    ))
    assert all(request.info == "x" * 50 for request in (
        awaited.args[0] for awaited in charge_point.call.await_args_list
    ))


def test_websocket_transaction_survives_reconnect(monkeypatch):
    messages = []
    openwb_cp = SimpleNamespace(
        num=1,
        data=SimpleNamespace(get=SimpleNamespace(
            fault_state=0,
            fault_str="",
            plug_state=True,
            imported=100,
            ocpp=SimpleNamespace(transaction_id=None, transaction_id_tag=None,
                                 tag_accepted=False, availability=[True, True],
                                 pending_availability=[False, False], pending_transactions=[],
                                 authorization_flow_status=None,
                                 test_reconnect=False,
                                 config=ocpp_config_factory()),
            serial_number="serial-1",
        ), config=SimpleNamespace(ocpp_chargebox_password="test-password")),
        get_ocpp_status=lambda: ChargePointStatus.available,
        get_ocpp_status_connector_0=lambda: ChargePointStatus.available,
        chargepoint_module=SimpleNamespace(config=SimpleNamespace(type="test-cp")),
    )
    monkeypatch.setattr(ocpp_client, "get_cp_from_chargebox_id", lambda _: openwb_cp)
    monkeypatch.setattr(ocpp_chargepoint, "get_cp_from_chargebox_id", lambda _: openwb_cp)
    monkeypatch.setattr(ocpp_connection_manager, "get_cp_from_chargebox_id", lambda _: openwb_cp)
    monkeypatch.setattr(ocpp_transaction_coordinator, "get_cp_from_chargebox_id", lambda _: openwb_cp)

    class FakeCsms(ServerChargePoint):
        @on(Action.boot_notification)
        async def boot(self, **kwargs):
            messages.append("BootNotification")
            return call_result.BootNotification(
                current_time="2026-09-30T12:00:00Z", interval=60,
                status=RegistrationStatus.accepted,
            )

        @on(Action.authorize)
        async def authorize(self, **kwargs):
            messages.append("Authorize")
            return call_result.Authorize(id_tag_info={"status": "Accepted"})

        @on(Action.start_transaction)
        async def start_transaction(self, **kwargs):
            messages.append("StartTransaction")
            return call_result.StartTransaction(
                transaction_id=42, id_tag_info={"status": "Accepted"},
            )

        @on(Action.meter_values)
        async def meter_values(self, **kwargs):
            messages.append("MeterValues")
            return call_result.MeterValues()

        @on(Action.stop_transaction)
        async def stop_transaction(self, **kwargs):
            messages.append("StopTransaction")
            return call_result.StopTransaction()

    async def check():
        async def accept(websocket, path):
            await FakeCsms(path.lstrip("/"), websocket).start()

        async with websockets.serve(accept, "127.0.0.1", 0, subprotocols=["ocpp1.6"]) as server:
            port = server.sockets[0].getsockname()[1]
            monkeypatch.setattr(data, "data", SimpleNamespace(
                cp_data={"cp1": openwb_cp},
                optional_data=SimpleNamespace(data=SimpleNamespace(ocpp=SimpleNamespace(
                    config=SimpleNamespace(
                        active=True,
                        url=f"ws://127.0.0.1:{port}",
                        version="ocpp1.6",
                    ),
                ))),
                system_data={"system": SimpleNamespace(data={"version": "test"})},
            ), raising=False)
            client = object.__new__(OcppClient)
            client._meter_snapshots = {}
            client.connection_manager = OcppConnectionManager(
                chargepoint_factory=client._created_charge_point,
                on_connected=client._initialize_connection,
                on_disconnected=client._connection_closed,
            )
            client.transactions = TransactionCoordinator(
                ensure_connected=client.connection_manager.connect,
            )

            connection = await client.connection_manager.connect("box-1")
            try:
                assert connection.boot_accepted is True
                assert await client.transactions.start("box-1", 1, "TAG", 100) is True
                connection = await client.connection_manager.reconnect_now("box-1")
                assert openwb_cp.data.get.ocpp.transaction_id == 42
                await connection.cp._meter_values(1, 42, [{
                    "timestamp": "2026-09-30T12:00:00Z",
                    "sampledValue": [{"value": "150", "unit": "Wh"}],
                }])
                assert await client.transactions.stop("box-1", 150, "", "EVDisconnected") is True
            finally:
                await client.connection_manager.disconnect("box-1")

    asyncio.run(check())

    assert messages == [
        "BootNotification", "Authorize", "StartTransaction", "BootNotification",
        "MeterValues", "StopTransaction",
    ]
    assert openwb_cp.data.get.ocpp.transaction_id is None
