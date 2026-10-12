import json
from unittest.mock import Mock

import pytest

from modules.vehicles.kia import api


def _status_response(target_soc=None):
    vehicle = {
        "Green": {
            "BatteryManagement": {"BatteryRemain": {"Ratio": 55}},
        },
        "Drivetrain": {
            "FuelSystem": {"DTE": {"Total": 300}},
            "Odometer": 12345,
        },
    }
    if target_soc is not None:
        vehicle["Green"]["ChargingInformation"] = {"TargetSoC": {"Standard": target_soc}}
    return json.dumps({"resMsg": {"state": {"Vehicle": vehicle}}})


class TestKiaApi:
    @pytest.fixture(autouse=True)
    def set_up(self, monkeypatch):
        monkeypatch.setattr(api, "getString", Mock(return_value="x"))
        monkeypatch.setattr(api, "getStamp", Mock(return_value="stamp"))
        monkeypatch.setattr(api.time, "sleep", Mock())

    def _call(self, monkeypatch, response_json):
        monkeypatch.setattr(api, "getHTTP", Mock(return_value=response_json))
        token = {"deviceId": "d", "gcmClientId": "c", "gcmVehicleId": "v",
                 "tokenType": "Bearer", "accessToken": "a"}
        return api.getStatusFull("vehicle-id", "control-token", token, "kia")

    def test_no_target_soc_has_no_warning(self, monkeypatch):
        result = self._call(monkeypatch, _status_response())
        assert result.warning is None
        assert result.soc == 55

    def test_target_soc_below_100_has_warning(self, monkeypatch):
        result = self._call(monkeypatch, _status_response(target_soc=80))
        assert result.warning is not None
        assert "80" in result.warning

    def test_target_soc_100_has_no_warning(self, monkeypatch):
        result = self._call(monkeypatch, _status_response(target_soc=100))
        assert result.warning is None
