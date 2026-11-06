import asyncio
import copy
from contextlib import asynccontextmanager
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from ocpp.v16.enums import UnlockStatus

from control.ocpp import ocpp_chargepoint, ocpp_client
from control.ocpp.ocpp_chargepoint import OcppChargePoint
from control.ocpp.ocpp_client import OcppClient
from modules.common import connector_unlock


@asynccontextmanager
async def _receiving_charge_point(monkeypatch, callback):
    monkeypatch.setattr(ocpp_chargepoint, "get_cp_from_chargebox_id", lambda _: SimpleNamespace(num=1))
    incoming = asyncio.Queue()
    outgoing = asyncio.Queue()
    websocket = SimpleNamespace(recv=incoming.get, send=outgoing.put)
    cp = OcppChargePoint("box", websocket, unlock_callback=callback)
    receiver = asyncio.create_task(cp.start())
    try:
        yield cp, incoming, outgoing
    finally:
        await cp.cancel_background_tasks()
        receiver.cancel()
        await asyncio.gather(receiver, return_exceptions=True)


@pytest.mark.parametrize("result,status", [("unlocked", "Unlocked"),
                                           ("failed", "UnlockFailed"),
                                           ("not_supported", "NotSupported")])
def test_unlock_keeps_receiving_call_results_until_hardware_finishes(monkeypatch, result, status):
    async def run():
        entered = asyncio.Event()
        release = asyncio.Event()

        async def unlock(chargebox_id):
            assert chargebox_id == "box"
            entered.set()
            await release.wait()
            return result

        callback = AsyncMock(side_effect=unlock)
        async with _receiving_charge_point(monkeypatch, callback) as (cp, incoming, outgoing):
            heartbeat = asyncio.create_task(cp._heartbeat())
            try:
                request = json.loads(await asyncio.wait_for(outgoing.get(), 1))
                assert request[0] == 2
                assert request[2] == "Heartbeat"
                await incoming.put(json.dumps([2, "unlock-1", "UnlockConnector", {"connectorId": 1}]))
                await asyncio.wait_for(entered.wait(), 1)

                await incoming.put(json.dumps([3, request[1], {"currentTime": "2026-10-23T12:00:00Z"}]))
                response = await asyncio.wait_for(heartbeat, 1)
                assert response.current_time == "2026-10-23T12:00:00Z"
                assert outgoing.empty()

                release.set()
                response = json.loads(await asyncio.wait_for(outgoing.get(), 1))
                assert response == [3, "unlock-1", {"status": status}]
                callback.assert_awaited_once_with("box")
            finally:
                heartbeat.cancel()
                await asyncio.gather(heartbeat, return_exceptions=True)

    asyncio.run(run())


@pytest.mark.parametrize("payload", [{}, {"connectorId": "invalid"}])
def test_invalid_unlock_payload_receives_call_error(monkeypatch, payload):
    callback = AsyncMock()

    async def run():
        async with _receiving_charge_point(monkeypatch, callback) as (_, incoming, outgoing):
            await incoming.put(json.dumps([2, "invalid-unlock", "UnlockConnector", payload]))
            response = json.loads(await asyncio.wait_for(outgoing.get(), 1))
            assert response[:2] == [4, "invalid-unlock"]
            callback.assert_not_awaited()

    asyncio.run(run())


def test_second_unlock_is_rejected_while_first_request_waits(monkeypatch):
    async def run():
        entered = asyncio.Event()
        release = asyncio.Event()

        async def unlock(_):
            entered.set()
            await release.wait()
            return "unlocked"

        callback = AsyncMock(side_effect=unlock)
        async with _receiving_charge_point(monkeypatch, callback) as (_, incoming, outgoing):
            await incoming.put(json.dumps([2, "first", "UnlockConnector", {"connectorId": 1}]))
            await asyncio.wait_for(entered.wait(), 1)
            await incoming.put(json.dumps([2, "second", "UnlockConnector", {"connectorId": 1}]))
            response = json.loads(await asyncio.wait_for(outgoing.get(), 1))
            assert response == [3, "second", {"status": "UnlockFailed"}]
            callback.assert_awaited_once_with("box")

            release.set()
            response = json.loads(await asyncio.wait_for(outgoing.get(), 1))
            assert response == [3, "first", {"status": "Unlocked"}]

    asyncio.run(run())


def test_connection_cleanup_cancels_waiting_unlock_request(monkeypatch):
    async def run():
        entered = asyncio.Event()
        cancelled = asyncio.Event()

        async def unlock(_):
            entered.set()
            try:
                await asyncio.Event().wait()
            finally:
                cancelled.set()

        async with _receiving_charge_point(monkeypatch, unlock) as (cp, incoming, outgoing):
            await incoming.put(json.dumps([2, "unlock", "UnlockConnector", {"connectorId": 1}]))
            await asyncio.wait_for(entered.wait(), 1)
            await asyncio.wait_for(cp.cancel_background_tasks(), 1)
            assert cancelled.is_set()
            assert not cp._background_tasks
            assert not cp._unlock_lock.locked()
            assert outgoing.empty()

    asyncio.run(run())


def test_invalid_connector_does_not_trigger_hardware(monkeypatch):
    monkeypatch.setattr(ocpp_chargepoint, "get_cp_from_chargebox_id", lambda _: SimpleNamespace(num=1))
    callback = AsyncMock()

    async def run():
        cp = OcppChargePoint("box", Mock(), unlock_callback=callback)
        return await cp.unlock_connector(0)
    assert asyncio.run(run()).status == UnlockStatus.not_supported
    callback.assert_not_called()


def test_client_sets_unlock_stop_and_leaves_transaction_stop_to_chargepoint(monkeypatch):
    module = SimpleNamespace(
        config=SimpleNamespace(type="internal_openwb", configuration=SimpleNamespace(mode="socket", duo_num=0)))
    request = AsyncMock(return_value="unlocked")
    monkeypatch.setattr(connector_unlock, "request_unlock", request)
    cp = SimpleNamespace(num=1, chargepoint_module=module,
                         data=SimpleNamespace(
                             get=SimpleNamespace(
                                 ocpp=SimpleNamespace(unlock_stop=False), imported=123)))
    monkeypatch.setattr(ocpp_client, "get_cp_from_chargebox_id", lambda _: cp)
    client = object.__new__(OcppClient)
    client._unlock_in_progress = set()
    client.transactions = Mock()
    client.transactions.get_id_tag.return_value = "tag"
    client.request_stop = Mock()
    assert asyncio.run(client._handle_unlock("box")) == "unlocked"
    assert cp.data.get.ocpp.unlock_stop
    client.transactions.block_start.assert_called_once_with("box")
    assert not client.is_unlock_in_progress("box")
    request.assert_awaited_once_with(0)
    client.request_stop.assert_not_called()


@pytest.mark.parametrize("outcome", ["unlocked", "failed", "error", "cancelled"])
def test_unlock_runtime_state_survives_model_replacement_and_is_always_cleared(monkeypatch, outcome):
    module = SimpleNamespace(
        config=SimpleNamespace(type="internal_openwb", configuration=SimpleNamespace(mode="socket", duo_num=0)))
    current = [SimpleNamespace(num=1, chargepoint_module=module,
                               data=SimpleNamespace(get=SimpleNamespace(ocpp=SimpleNamespace(unlock_stop=False))))]
    monkeypatch.setattr(ocpp_client, "get_cp_from_chargebox_id", lambda _: current[0])
    client = object.__new__(OcppClient)
    client._unlock_in_progress = set()
    client.transactions = Mock()

    async def check():
        entered = asyncio.Event()
        release = asyncio.Event()

        async def unlock(_):
            entered.set()
            await release.wait()
            if outcome == "error":
                raise RuntimeError("Hardwarefehler")
            return outcome

        request = AsyncMock(side_effect=unlock)
        monkeypatch.setattr(connector_unlock, "request_unlock", request)
        task = asyncio.create_task(client._handle_unlock("box"))
        try:
            await asyncio.wait_for(entered.wait(), 1)
            assert client.is_unlock_in_progress("box")
            assert not client.is_unlock_in_progress("other-box")
            current[0] = copy.deepcopy(current[0])
            assert client.is_unlock_in_progress("box")
            # Auch ein zweiter Callback darf den Zustand des ersten nicht entfernen.
            assert await client._handle_unlock("box") == "failed"
            assert client.is_unlock_in_progress("box")
            request.assert_awaited_once_with(0)
            # Ein zuvor vom Backend eingereihter Rücksetzauftrag darf während
            # der Entriegelung auch im OCPP-Loop keine Startsperre löschen.
            await client._clear_start_block("box")
            client.transactions.clear_start_block.assert_not_called()

            if outcome == "cancelled":
                task.cancel()
                with pytest.raises(asyncio.CancelledError):
                    await task
            else:
                release.set()
                if outcome == "error":
                    with pytest.raises(RuntimeError, match="Hardwarefehler"):
                        await task
                else:
                    assert await task == outcome
            assert not client.is_unlock_in_progress("box")
            client.transactions.clear_start_block.return_value = False
            await client._clear_start_block("box")
            client.transactions.clear_start_block.assert_called_once_with("box")
            # Die Stop-Sperre bleibt bis zum anschließenden Absteck-Update bestehen.
            assert current[0].data.get.ocpp.unlock_stop is True
        finally:
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)

    asyncio.run(check())


@pytest.mark.parametrize("configuration",
                         [SimpleNamespace(), SimpleNamespace(mode=None), SimpleNamespace(mode="series")])
def test_client_requires_socket_mode_without_capability_topic(monkeypatch, configuration):
    module = SimpleNamespace(config=SimpleNamespace(type="internal_openwb", configuration=configuration))
    request = AsyncMock()
    monkeypatch.setattr(connector_unlock, "request_unlock", request)
    cp = SimpleNamespace(chargepoint_module=module)
    monkeypatch.setattr(ocpp_client, "get_cp_from_chargebox_id", lambda _: cp)
    client = object.__new__(OcppClient)
    client.transactions = Mock()
    client.request_stop = Mock()
    assert asyncio.run(client._handle_unlock("box")) == "not_supported"
    client.transactions.block_start.assert_not_called()
    client.request_stop.assert_not_called()
    request.assert_not_called()


def test_external_chargepoint_cannot_target_local_hardware(monkeypatch):
    module = SimpleNamespace(config=SimpleNamespace(type="external_openwb",
                             configuration=SimpleNamespace(mode="socket")))
    monkeypatch.setattr(ocpp_client, "get_cp_from_chargebox_id", lambda _: SimpleNamespace(chargepoint_module=module))
    request = AsyncMock()
    monkeypatch.setattr(connector_unlock, "request_unlock", request)
    assert asyncio.run(object.__new__(OcppClient)._handle_unlock("box")) == "not_supported"
    request.assert_not_called()
