import copy
from unittest.mock import MagicMock, Mock

import pytest

from modules.common.abstract_vehicle import VehicleUpdateData
from modules.common.configurable_vehicle import SocSource
from modules.vehicles.vweuda import libeuda, soc
from modules.vehicles.vweuda.config import VWEUDA, VWEUDAConfiguration

VIN = "WVW00000000000001"
SOC_KEY = "ac1108b1-b8cc-3db9-a663-03d387e42223"


def payload(value=55, timestamp="2026-10-19T10:00:00Z", odometer=None):
    return {"vin": VIN, "Data": [
        {"key": SOC_KEY, "dataFieldName": "soc", "value": value},
        {"key": "ts", "dataFieldName": "car_captured_time", "value": timestamp},
        {"key": "41c0805c-43e5-313e-9dfb-356cb8d20f7c", "dataFieldName": "odometer", "value": odometer},
    ]}


@pytest.fixture
def config():
    return VWEUDA(configuration=VWEUDAConfiguration(user_id="test@example.com", password="test", vin=VIN))


def test_history_keeps_valid_data_and_processes_each_dataset_once(config):
    portal = libeuda.EudaVehicle(config.configuration, 1)
    client = Mock()
    client.get_metadata.return_value = {"Identifier": "id"}
    client.list_datasets.return_value = [
        {"name": "new.zip", "createdOn": "2026-10-19T12:00:00Z"},
        {"name": "empty_no_content_found.zip"},
        {"name": "old.zip", "createdOn": "2026-10-19T10:00:00Z"},
        {"name": "incomplete.zip", "createdOn": "2026-10-19T11:00:00Z"},
    ]
    contents = {"old.zip": payload(odometer=1000), "incomplete.zip": payload(value=None),
                "new.zip": payload(value=60, timestamp="2026-10-19T12:00:00Z")}
    client.download_dataset.side_effect = lambda vin, identifier, name: (VIN + name + ".json", contents[name])
    portal._poll(client)
    assert [call.args[2] for call in client.download_dataset.call_args_list] == [
        "old.zip", "incomplete.zip", "new.zip"]
    assert portal._result["soc"] == 60
    assert portal._result["odometer"] == 1000
    portal._poll(client)
    assert client.download_dataset.call_count == 3


@pytest.mark.parametrize("value", [None, "bad", -1, 101, "NaN", "Infinity"])
def test_invalid_data_never_advances_valid_timestamp(config, value):
    portal = libeuda.EudaVehicle(config.configuration, 1)
    portal._merge(libeuda.parse_vehicle_data(payload()))
    before = dict(portal._result)
    assert not portal._merge(libeuda.parse_vehicle_data(payload(value, "2026-10-19T12:00:00Z")))
    assert portal._result == before


def test_missing_timestamp_and_older_data_do_not_replace_cache(config):
    portal = libeuda.EudaVehicle(config.configuration, 1)
    portal._merge(libeuda.parse_vehicle_data(payload()))
    assert not portal._merge(libeuda.parse_vehicle_data(payload(60, None)))
    assert not portal._merge(libeuda.parse_vehicle_data(payload(60, "2026-10-19T09:00:00Z")))
    assert portal._result["soc"] == 55


def test_zero_values_and_missing_optional_fields_are_preserved_in_memory(config):
    portal = libeuda.EudaVehicle(config.configuration, 1)
    first = libeuda.parse_vehicle_data(payload(odometer=1000))
    first["range"] = 200
    portal._merge(first)
    newer = libeuda.parse_vehicle_data(payload(0, "2026-10-19T11:00:00Z", odometer=900))
    portal._merge(newer)
    assert portal._result["range"] == 200
    newer["range"] = 0
    portal._merge(newer)
    assert portal._result["soc"] == 0
    assert portal._result["range"] == 0
    assert portal._result["odometer"] == 1000


@pytest.mark.parametrize("has_cache", [False, True])
def test_scheduler_copies_share_cache_retry_flag_and_recovery(config, monkeypatch, has_cache):
    config.configuration.calculate_soc = True
    requests = []

    def poll(portal, client):
        requests.append(client)
        if len(requests) == 1:
            if has_cache:
                portal._merge(libeuda.parse_vehicle_data(payload()))
            raise libeuda.ApiError("Portal unavailable")
        portal._merge(libeuda.parse_vehicle_data(payload(60, "2026-10-19T11:00:00Z")))

    monkeypatch.setattr(libeuda.EudaVehicle, "_poll", poll)
    session_factory = MagicMock()
    monkeypatch.setattr(libeuda.req, "get_http_session", session_factory)
    module = soc.create_vehicle(config, 1)
    first = copy.deepcopy(module)
    if has_cache:
        state = first._get_carstate_by_source(VehicleUpdateData(), SocSource.API)
        assert state.soc == 55
        assert state.soc_timestamp == 1792404000
        assert "Portal unavailable" in state.warning
    else:
        with pytest.raises(Exception, match="Portal unavailable"):
            first._get_carstate_by_source(VehicleUpdateData(), SocSource.API)
    assert module.get_request_interval_override() == 60
    second = copy.deepcopy(module)
    assert second._get_carstate_source(VehicleUpdateData(charge_state=True)) == SocSource.API
    state = second._get_carstate_by_source(VehicleUpdateData(), SocSource.API)
    assert state.soc == 60
    assert state.warning is None
    assert module.get_request_interval_override() is None
    assert module._get_carstate_source(VehicleUpdateData(charge_state=True)) == SocSource.CALCULATION
    assert session_factory.call_count == 2
    assert session_factory.return_value.__exit__.call_count == 2
    assert soc.create_vehicle(config, 1).get_request_interval_override() is None


def test_empty_portal_response_without_cache_is_error_and_requests_retry(config, monkeypatch):
    client = Mock()
    client.get_metadata.return_value = {"Identifier": "id"}
    client.list_datasets.return_value = []
    monkeypatch.setattr(libeuda, "EudaApiClient", Mock(return_value=client))
    portal = libeuda.EudaVehicle(config.configuration, 1)
    with pytest.raises(libeuda.ApiError, match="keine Datenpakete"):
        portal.fetch(VehicleUpdateData())
    assert portal.get_request_interval_override() == 60


def test_foreign_and_corrupt_datasets_do_not_block_later_valid_data(config):
    client = Mock()
    client.get_metadata.return_value = {"Identifier": "id"}
    client.list_datasets.return_value = [{"name": name} for name in ("bad.zip", "foreign.zip", "good.zip")]
    foreign = dict(payload(), vin="WVW00000000000002")
    client.download_dataset.side_effect = [libeuda.DatasetError("bad archive"),
                                           ("foreign.json", foreign), (VIN + ".json", payload())]
    portal = libeuda.EudaVehicle(config.configuration, 1)
    portal._poll(client)
    assert portal._result["soc"] == 55


def test_memory_cache_used_with_original_timestamp_and_calculated_range_on_failure(config, monkeypatch):
    portal = libeuda.EudaVehicle(config.configuration, 1)
    portal._merge(libeuda.parse_vehicle_data(payload()))
    timestamp = portal._result["soc_timestamp"]
    monkeypatch.setattr(libeuda.EudaVehicle, "_poll", Mock(side_effect=libeuda.ApiError("offline")))
    state = portal.fetch(VehicleUpdateData(battery_capacity=80, average_consump=20))
    assert state.soc == 55
    assert state.range == 220
    assert state.soc_timestamp == timestamp
    assert "offline" in state.warning
    assert portal.get_request_interval_override() == 60

    # A fresh module starts without measurements and must fetch from the portal.
    replacement = libeuda.EudaVehicle(config.configuration, 1)
    with pytest.raises(libeuda.ApiError, match="offline"):
        replacement.fetch(VehicleUpdateData())
    assert replacement.get_request_interval_override() == 60


def test_unexpected_error_logs_traceback_and_keeps_cache_retry(config, monkeypatch, caplog):
    portal = libeuda.EudaVehicle(config.configuration, 1)
    portal._merge(libeuda.parse_vehicle_data(payload()))
    monkeypatch.setattr(portal, "_poll", Mock(side_effect=RuntimeError("unexpected response shape")))
    state = portal.fetch(VehicleUpdateData())
    assert state.soc == 55
    assert "unexpected response shape" in state.warning
    assert portal.get_request_interval_override() == 60
    assert any(record.exc_info and "Unerwarteter Fehler" in record.getMessage() for record in caplog.records)
