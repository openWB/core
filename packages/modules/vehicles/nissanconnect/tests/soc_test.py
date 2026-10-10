import importlib
import sys
from types import ModuleType
from unittest.mock import Mock

import pytest

from modules.vehicles.nissanconnect.src.api import BatteryStatus
from modules.vehicles.nissanconnect.config import NissanConnect, NissanConnectConfiguration


@pytest.fixture
def soc_module(monkeypatch):
    # The standalone suite must not bootstrap openWB services on the test PC.
    # In the normal core suite this dependency is already imported by conftest.
    dependency = "modules.common.configurable_vehicle"
    if dependency not in sys.modules:
        stub = ModuleType(dependency)
        stub.ConfigurableVehicle = Mock()
        monkeypatch.setitem(sys.modules, dependency, stub)
    return importlib.import_module("modules.vehicles.nissanconnect.soc")


def test_openwb_adapter_preserves_timestamp_reuses_client_and_handles_config_change(monkeypatch, soc_module):
    soc = soc_module

    # Only replace the scheduling/storage wrapper; use the real CarState and updater.
    wrapper = Mock()
    monkeypatch.setattr(soc, "ConfigurableVehicle", wrapper)
    fake_client = Mock()
    fake_client.fetch_battery.return_value = BatteryStatus(0, 1640995200, 0, 12345.6)
    factory = Mock(return_value=fake_client)
    monkeypatch.setattr(soc, "NissanClient", factory)
    config = NissanConnect(configuration=NissanConnectConfiguration("synthetic@example.invalid", "synthetic-password"))
    soc.create_vehicle(config, 7)
    updater = wrapper.call_args.kwargs["component_updater"]
    state = updater(None)
    assert (state.soc, state.range, state.soc_timestamp, state.odometer) == (0, 0, 1640995200, 12345.6)
    fake_client.fetch_battery.assert_called_once_with(include_odometer=True)
    updater(None)
    assert factory.call_count == 1
    config.configuration.password = "synthetic-new-password"
    updater(None)
    assert factory.call_count == 2
    assert factory.call_args_list[0].kwargs["request_counter"] is factory.call_args_list[1].kwargs["request_counter"]
    soc.create_vehicle(config, 8)
    wrapper.call_args.kwargs["component_updater"](None)
    assert factory.call_args.kwargs["request_counter"] is not factory.call_args_list[0].kwargs["request_counter"]
    assert wrapper.call_args.kwargs["calc_while_charging"] is False
    assert wrapper.call_args_list[0].kwargs["vehicle"] == 7


def test_configuration_descriptor_and_module_name_agree(soc_module):
    config = soc_module.device_descriptor.configuration_factory()
    assert config.type == "nissanconnect"
    assert config.configuration.vin is None


def test_configuration_roundtrip_uses_openwb_serializer():
    from dataclass_utils import asdict, dataclass_from_dict

    config = NissanConnect(configuration=NissanConnectConfiguration(
        "synthetic@example.invalid", "synthetic-password", "SJNFAAZE1U0000001"))
    encoded = asdict(config)
    decoded = dataclass_from_dict(NissanConnect, encoded)
    assert decoded.type == "nissanconnect"
    assert isinstance(decoded.configuration, NissanConnectConfiguration)
    assert decoded.configuration.user_id == config.configuration.user_id
    assert decoded.configuration.password == config.configuration.password
    assert decoded.configuration.vin == config.configuration.vin


def test_module_logs_only_allowlisted_diagnostics(monkeypatch, soc_module, caplog):
    import json
    import logging
    from modules.vehicles.nissanconnect.tests.helpers import VIN, full_script, make_client, reply
    from modules.vehicles.nissanconnect.src.api import NissanError

    client, transport, _ = make_client(full_script() + [reply({"data": {"attributes": {"totalMileage": 12345.6}}})])
    wrapper = Mock()
    monkeypatch.setattr(soc_module, "ConfigurableVehicle", wrapper)

    def create_client(*args, **kwargs):
        client._request_counter = kwargs["request_counter"]
        return client
    monkeypatch.setattr(soc_module, "NissanClient", create_client)
    config = NissanConnect(configuration=NissanConnectConfiguration("synthetic@example.invalid", "synthetic-password"))
    soc_module.create_vehicle(config, 7)
    updater = wrapper.call_args.kwargs["component_updater"]
    caplog.set_level(logging.DEBUG, logger=soc_module.__name__)
    updater(None)
    assert len(caplog.records) == 1
    assert '"outcome": "success"' in caplog.text and '"data_age_seconds": 86400' in caplog.text
    assert '"soc": 47.0' in caplog.text and 'Nissan vehicle 7' in caplog.text
    summary = json.loads(caplog.records[0].args[1])
    assert summary["http_requests_last_24h"] == 8
    assert summary["http_requests_since_start"] == 8
    assert summary["http_requests_since_midnight"] == 8
    assert summary["http_requests_last_24h_complete"] is False
    for value in (VIN, "example.invalid", "synthetic-password", "synthetic-access", "synthetic-refresh"):
        assert value not in caplog.text
    assert not any(record.exc_info for record in caplog.records)

    # A deferred call is logged as such, without a new contact or measured value.
    client._retry_at_monotonic_seconds = 300
    client._retry_reason = "Synthetic wait."
    calls = len(transport.calls)
    with pytest.raises(NissanError):
        updater(None)
    assert len(transport.calls) == calls
    assert '"outcome": "deferred"' in caplog.records[-1].getMessage()
    deferred = json.loads(caplog.records[-1].args[1])
    assert deferred["request_started_at"] is None
    assert deferred["http_requests"] == 0
    assert deferred["http_requests_last_24h"] == 8
    assert deferred["http_requests_since_start"] == 8
