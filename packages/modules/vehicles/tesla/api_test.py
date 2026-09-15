import json

import pytest

from modules.vehicles.tesla import api
from modules.vehicles.tesla.config import TeslaSocToken


def _response(charge_limit_soc=None):
    charge_state = {
        "battery_level": "55",
        "battery_range": "200",
        "timestamp": "1652683252000",
    }
    if charge_limit_soc is not None:
        charge_state["charge_limit_soc"] = charge_limit_soc
    return json.dumps({
        "response": {
            "charge_state": charge_state,
            "vehicle_state": {"odometer": "1000"},
        }
    })


class TestTeslaApi:
    @pytest.fixture(autouse=True)
    def set_up(self, monkeypatch):
        monkeypatch.setattr(api, "__get_vehicle_id", lambda vehicle, token: "vehicle-id")

    def test_request_data_without_charge_limit_has_no_warning(self, monkeypatch):
        monkeypatch.setattr(api, "__request_data", lambda data_part, token: _response())

        soc, range, soc_timestamp, odometer, warning = api.request_data(0, TeslaSocToken())

        assert soc == 55.0
        assert warning is None

    def test_request_data_with_charge_limit_below_100_has_warning(self, monkeypatch):
        monkeypatch.setattr(api, "__request_data", lambda data_part, token: _response(charge_limit_soc=80))

        *_, warning = api.request_data(0, TeslaSocToken())

        assert warning is not None
        assert "80" in warning

    def test_request_data_with_charge_limit_100_has_no_warning(self, monkeypatch):
        monkeypatch.setattr(api, "__request_data", lambda data_part, token: _response(charge_limit_soc=100))

        *_, warning = api.request_data(0, TeslaSocToken())

        assert warning is None
