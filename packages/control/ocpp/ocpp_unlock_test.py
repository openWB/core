import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from ocpp.v16.enums import UnlockStatus

from control.ocpp import ocpp_chargepoint, ocpp_client
from control.ocpp.ocpp_chargepoint import OcppChargePoint
from control.ocpp.ocpp_client import OcppClient
from modules.common import connector_unlock


@pytest.mark.parametrize("result,status", [("unlocked", UnlockStatus.unlocked),
                                           ("failed", UnlockStatus.unlock_failed),
                                           ("not_supported", UnlockStatus.not_supported)])
def test_ocpp_reports_actual_hardware_result(monkeypatch, result, status):
    monkeypatch.setattr(ocpp_chargepoint, "get_cp_from_chargebox_id", lambda _: SimpleNamespace(num=1))
    callback = AsyncMock(return_value=result)

    async def run():
        cp = OcppChargePoint("box", Mock(), unlock_callback=callback)
        return await cp.unlock_connector(1)
    assert asyncio.run(run()).status == status
    callback.assert_awaited_once_with("box")


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
    client.transactions = Mock()
    client.transactions.get_id_tag.return_value = "tag"
    client.request_stop = Mock()
    assert asyncio.run(client._handle_unlock("box")) == "unlocked"
    assert cp.data.get.ocpp.unlock_stop
    client.transactions.block_start.assert_called_once_with("box")
    assert not cp.data.get.ocpp.unlock_in_progress
    request.assert_awaited_once_with(0)
    client.request_stop.assert_not_called()


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
