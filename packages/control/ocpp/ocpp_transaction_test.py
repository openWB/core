import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, call

import pytest
import websockets

from control import data
from control.chargepoint.chargepoint_data import ocpp_config_factory
from control.ocpp import ocpp_client
from control.ocpp import ocpp_chargepoint
from control.ocpp import ocpp_connection_manager
from control.ocpp import ocpp_transaction_coordinator
from control.ocpp.ocpp_chargepoint import OcppChargePoint
from control.ocpp.ocpp_client import OcppClient
from control.ocpp.ocpp_connection_manager import OcppConnectionManager
from control.ocpp.ocpp_transaction_coordinator import TransactionCoordinator, TransactionState
from ocpp.v16.enums import (AvailabilityStatus, AvailabilityType, ChargePointStatus,
                            ConfigurationStatus, RegistrationStatus, Action)
from ocpp.v16 import ChargePoint as ServerChargePoint, call_result
from ocpp.routing import on


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
        data=SimpleNamespace(get=SimpleNamespace(ocpp=SimpleNamespace(
            transaction_id=None,
            transaction_id_tag=None,
            tag_accepted=False,
            availability=True,
            pending_transactions=[],
            pending_availability=False,
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
        _stop_transaction=AsyncMock(),
    )
    connection = SimpleNamespace(cp=charge_point, boot_accepted=True)
    ensure_connected = AsyncMock(return_value=connection)
    coordinator = TransactionCoordinator(ensure_connected=ensure_connected)
    monkeypatch.setattr(ocpp_transaction_coordinator, "get_cp_from_chargebox_id", lambda _: openwb_cp)
    return coordinator, connection, openwb_cp


def test_start_publishes_active_transaction(transaction_setup, mock_pub):
    coordinator, connection, openwb_cp = transaction_setup

    result = asyncio.run(coordinator.start("box-1", 1, "TAG", 100))

    assert result is True
    assert coordinator.get_state("box-1") == TransactionState.ACTIVE
    assert coordinator.get_transaction_id("box-1") == 42
    assert openwb_cp.data.get.ocpp.transaction_id == 42
    assert openwb_cp.data.get.ocpp.tag_accepted is True
    connection.cp._authorize.assert_awaited_once_with(id_tag="TAG")
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

    assert asyncio.run(coordinator.start("box-1", 1, "TAG", 100)) is True

    assert coordinator.get_state("box-1") == TransactionState.REJECTED
    assert openwb_cp.data.get.ocpp.tag_accepted is False
    assert openwb_cp.data.get.ocpp.transaction_id is None
    if rejected_step == "authorize":
        connection.cp._start_transaction.assert_not_awaited()


def test_start_response_error_does_not_retry_same_tag(transaction_setup):
    coordinator, connection, openwb_cp = transaction_setup
    connection.cp._start_transaction.side_effect = RuntimeError("response lost")

    async def check():
        assert await coordinator.start("box-1", 1, "TAG", 100) is False
        assert await coordinator.start("box-1", 1, "TAG", 100) is False

    asyncio.run(check())

    assert coordinator.get_state("box-1") == TransactionState.ERROR
    assert openwb_cp.data.get.ocpp.tag_accepted is False
    connection.cp._start_transaction.assert_awaited_once()


@pytest.mark.parametrize("waiting_for", ["authorize", "start"])
def test_stop_during_start_is_not_lost(transaction_setup, waiting_for):
    coordinator, connection, openwb_cp = transaction_setup
    original = getattr(connection.cp, f"_{waiting_for}" if waiting_for == "authorize" else "_start_transaction")

    async def check():
        entered = asyncio.Event()
        release = asyncio.Event()

        async def delayed(**kwargs):
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
        release.set()
        await start

    asyncio.run(check())

    if waiting_for == "authorize":
        connection.cp._start_transaction.assert_not_awaited()
        connection.cp._stop_transaction.assert_not_awaited()
    else:
        connection.cp._stop_transaction.assert_awaited_once_with(
            meter_stop=150, transaction_id=42, reason="EVDisconnected", id_tag="TAG",
        )
        assert coordinator.get_state("box-1") == TransactionState.IDLE
        assert openwb_cp.data.get.ocpp.transaction_id is None
        assert openwb_cp.data.get.ocpp.tag_accepted is False


def test_active_stop_clears_transaction_only_after_response(transaction_setup):
    coordinator, connection, openwb_cp = transaction_setup

    async def check():
        entered = asyncio.Event()
        release = asyncio.Event()

        async def delayed_stop(**kwargs):
            entered.set()
            await release.wait()

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


def test_failed_stop_keeps_transaction_id(transaction_setup):
    coordinator, connection, openwb_cp = transaction_setup
    connection.cp._stop_transaction.side_effect = RuntimeError("response lost")

    async def check():
        await coordinator.start("box-1", 1, "TAG", 100)
        assert await coordinator.stop("box-1", 150, "", "EVDisconnected") is False

    asyncio.run(check())

    assert coordinator.get_state("box-1") == TransactionState.ERROR
    assert coordinator.get_transaction_id("box-1") == 42
    assert openwb_cp.data.get.ocpp.transaction_id == 42


def test_offline_stop_is_replayed_once_after_reconnect(transaction_setup, mock_pub):
    coordinator, connection, openwb_cp = transaction_setup

    async def check():
        await coordinator.start("box-1", 1, "TAG", 100)
        coordinator._ensure_connected.return_value = None
        assert await coordinator.stop("box-1", 150, "", "EVDisconnected") is False
        assert openwb_cp.data.get.ocpp.pending_transactions == [{
            "action": "stop", "transaction_id": 42, "id_tag": "TAG",
            "imported": 150, "reason": "EVDisconnected",
        }]
        coordinator._ensure_connected.return_value = connection
        transaction_id_publications_before_replay = mock_pub.pub.call_args_list.count(
            call("openWB/set/chargepoint/1/get/ocpp/transaction_id", 42)
        )
        await coordinator.on_connected("box-1", connection)
        await coordinator.on_connected("box-1", connection)
        return transaction_id_publications_before_replay

    transaction_id_publications_before_replay = asyncio.run(check())

    connection.cp._stop_transaction.assert_awaited_once_with(
        meter_stop=150, transaction_id=42, reason="EVDisconnected", id_tag="TAG",
    )
    assert openwb_cp.data.get.ocpp.pending_transactions == []
    assert coordinator.get_state("box-1") == TransactionState.IDLE
    assert mock_pub.pub.call_args_list.count(
        call("openWB/set/chargepoint/1/get/ocpp/pending_transactions", [])
    ) == 1
    assert mock_pub.pub.call_args_list.count(
        call("openWB/set/chargepoint/1/get/ocpp/transaction_id", 42)
    ) == transaction_id_publications_before_replay


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


@pytest.fixture
def handler_setup(monkeypatch):
    openwb_cp = SimpleNamespace(
        num=1,
        data=SimpleNamespace(get=SimpleNamespace(ocpp=SimpleNamespace(
            transaction_id=None, availability=True, pending_availability=False,
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
def test_inoperative_availability_is_scheduled_until_stop(handler_setup, mock_pub, connector_id):
    make_charge_point, openwb_cp = handler_setup
    openwb_cp.data.get.ocpp.transaction_id = 42

    async def check():
        charge_point = make_charge_point()
        result = await charge_point.on_change_availability(
            connector_id, AvailabilityType.inoperative,
        )
        assert result.status == AvailabilityStatus.scheduled
        assert openwb_cp.data.get.ocpp.availability is True
        assert openwb_cp.data.get.ocpp.pending_availability is True
        await charge_point.apply_pending_availability()

    asyncio.run(check())

    assert openwb_cp.data.get.ocpp.availability is False
    assert openwb_cp.data.get.ocpp.pending_availability is False
    mock_pub.pub.assert_any_call("openWB/set/chargepoint/1/get/ocpp/availability", False)


def test_change_availability_rejects_unknown_connector(handler_setup):
    make_charge_point, openwb_cp = handler_setup

    async def check():
        charge_point = make_charge_point()
        return await charge_point.on_change_availability(2, AvailabilityType.inoperative)

    result = asyncio.run(check())

    assert result.status == AvailabilityStatus.rejected
    assert openwb_cp.data.get.ocpp.availability is True


def test_immediate_availability_change_clears_pending_request(handler_setup, mock_pub):
    make_charge_point, openwb_cp = handler_setup
    openwb_cp.data.get.ocpp.pending_availability = True

    async def check():
        charge_point = make_charge_point()
        return await charge_point.on_change_availability(1, AvailabilityType.inoperative)

    response = asyncio.run(check())

    assert response.status == AvailabilityStatus.accepted
    assert openwb_cp.data.get.ocpp.availability is False
    assert openwb_cp.data.get.ocpp.pending_availability is False
    mock_pub.pub.assert_any_call(
        "openWB/set/chargepoint/1/get/ocpp/pending_availability",
        False,
    )


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

    assert response.configuration_key[0].key == "HeartbeatInterval"
    assert response.configuration_key[0].value == "10"
    assert response.configuration_key[0].readonly is True
    assert response.unknown_key == []


def test_change_configuration_rejects_readonly_parameter(handler_setup):
    make_charge_point, openwb_cp = handler_setup

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


def test_valid_configuration_interval_is_used(handler_setup):
    make_charge_point, _ = handler_setup

    async def check():
        charge_point = make_charge_point()
        response = await charge_point.change_configuration("MeterValueSampleInterval", "30")
        assert charge_point.openwb_cp.data.get.ocpp.config.MeterValueSampleInterval["value"] == 30
        return response

    response = asyncio.run(check())

    assert response.status == ConfigurationStatus.accepted


def test_set_configuration_value_publishes_parameter_dictionary(handler_setup, mock_pub):
    make_charge_point, openwb_cp = handler_setup

    async def check():
        charge_point = make_charge_point()
        await charge_point.set_configuration_value("MeterValueSampleInterval", 30)

    asyncio.run(check())

    expected_config = {
        "HeartbeatInterval": {
            "value": 10,
            "readonly": True,
            "type": "int",
        },
        "MeterValueSampleInterval": {
            "value": 30,
            "readonly": False,
            "type": "int",
        },
    }
    assert expected_config["MeterValueSampleInterval"] == {
        "value": 30,
        "readonly": False,
        "type": "int",
    }
    mock_pub.pub.assert_called_once_with(
        "openWB/set/chargepoint/1/get/ocpp/config",
        expected_config,
    )


def test_status_notification_sends_each_requested_message(handler_setup):
    make_charge_point, _ = handler_setup

    async def check():
        charge_point = make_charge_point()
        for force in (False, False, True):
            await charge_point._status_notification(
                connector_id=1, fault_state=0, fault_state_str="",
                status=ChargePointStatus.available, force=force,
            )
        return charge_point

    charge_point = asyncio.run(check())

    assert charge_point.call.await_count == 3
    assert all(request.connector_id == 1 for request in (
        awaited.args[0] for awaited in charge_point.call.await_args_list
    ))


def test_websocket_transaction_survives_reconnect(monkeypatch):
    messages = []
    openwb_cp = SimpleNamespace(
        num=1,
        data=SimpleNamespace(get=SimpleNamespace(
            ocpp=SimpleNamespace(transaction_id=None, transaction_id_tag=None,
                                 tag_accepted=False, availability=True,
                                 pending_availability=False, pending_transactions=[],
                                 test_reconnect=False,
                                 config=ocpp_config_factory()),
            serial_number="serial-1",
        )),
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
                optional_data=SimpleNamespace(data=SimpleNamespace(ocpp=SimpleNamespace(
                    config=SimpleNamespace(url=f"ws://127.0.0.1:{port}", version="ocpp1.6"),
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
