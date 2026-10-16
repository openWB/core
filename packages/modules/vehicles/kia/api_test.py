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


class TestCciHeaders:
    def test_bearer_prefix_is_not_duplicated(self, monkeypatch):
        monkeypatch.setattr(api, "getString", Mock(return_value="x"))
        headers = api.getCciHeaders("kia", "device-1", cci_access_token="Bearer abc123")
        assert headers["authorization"] == "Bearer abc123"

    def test_no_body_sets_content_length_zero(self, monkeypatch):
        monkeypatch.setattr(api, "getString", Mock(return_value="x"))
        headers = api.getCciHeaders("kia", "device-1")
        assert headers["Content-Length"] == "0"
        assert "Content-Type" not in headers

    def test_exchangeable_token_sets_non_ccs_header(self, monkeypatch):
        monkeypatch.setattr(api, "getString", Mock(return_value="x"))
        headers = api.getCciHeaders("kia", "device-1", non_ccs_token="ncs", exchangeable_token="ex")
        assert headers["exchangeable-token"] == "ex"
        assert headers["non-ccs-token"] == "ncs"
        assert headers["Authentication"] == "ncs"


class TestExchangeCciToken:
    def test_raises_on_non_200(self, monkeypatch):
        monkeypatch.setattr(api, "getString", Mock(return_value="https://cci-api-eu.kia.com"))
        monkeypatch.setattr(api.requests, "post", Mock(return_value=Mock(status_code=400, text="bad request")))
        with pytest.raises(RuntimeError):
            api.exchangeCciToken("auth-code", "device-1", "kia")

    def test_returns_expected_fields(self, monkeypatch):
        monkeypatch.setattr(api, "getString", Mock(return_value="https://cci-api-eu.kia.com"))
        response = Mock(status_code=200)
        response.json.return_value = {
            "accessToken": "cci-access", "refreshToken": "cci-refresh",
            "nonCcsToken": "ncs", "exchangeableAccessToken": "ex-access",
            "exchangeableRefreshToken": "ex-refresh", "nonCcsRefreshToken": "ncs-refresh",
            "idToken": "id-1",
        }
        monkeypatch.setattr(api.requests, "post", Mock(return_value=response))
        result = api.exchangeCciToken("auth-code", "device-1", "kia")
        assert result["cciAccessToken"] == "cci-access"
        assert result["nonCcsToken"] == "ncs"
        assert result["idToken"] == "id-1"


class TestExchangeCcsToken:
    def test_raises_on_non_200(self, monkeypatch):
        monkeypatch.setattr(api, "getString", Mock(return_value="https://cci-api-eu.kia.com"))
        monkeypatch.setattr(api.requests, "post", Mock(return_value=Mock(status_code=403, text="forbidden")))
        with pytest.raises(RuntimeError):
            api.exchangeCcsToken("device-1", "cci-access", "ncs", "ex-access", "kia")

    def test_raises_when_no_access_token_in_response(self, monkeypatch):
        monkeypatch.setattr(api, "getString", Mock(return_value="https://cci-api-eu.kia.com"))
        response = Mock(status_code=200, text="{}")
        response.json.return_value = {}
        monkeypatch.setattr(api.requests, "post", Mock(return_value=response))
        with pytest.raises(RuntimeError):
            api.exchangeCcsToken("device-1", "cci-access", "ncs", "ex-access", "kia")

    def test_returns_ccs_token(self, monkeypatch):
        monkeypatch.setattr(api, "getString", Mock(return_value="https://cci-api-eu.kia.com"))
        response = Mock(status_code=200)
        response.json.return_value = {"accessToken": "ccs-token-value"}
        monkeypatch.setattr(api.requests, "post", Mock(return_value=response))
        result = api.exchangeCcsToken("device-1", "cci-access", "ncs", "ex-access", "kia")
        assert result == "ccs-token-value"


class TestRefreshCciToken:
    def _token(self):
        return {"cciAccessToken": "old", "cciRefreshToken": "old-r", "nonCcsToken": "old-n",
                "exchangeableAccessToken": "e", "exchangeableRefreshToken": "er",
                "nonCcsRefreshToken": "nr", "idToken": "i", "deviceId": "d"}

    def test_raises_on_non_200(self, monkeypatch):
        monkeypatch.setattr(api, "getString", Mock(return_value="https://cci-api-eu.kia.com"))
        monkeypatch.setattr(api.requests, "post", Mock(return_value=Mock(status_code=401, text="unauthorized")))
        with pytest.raises(RuntimeError):
            api.refreshCciToken(self._token(), "kia")

    def test_updates_token_and_reexchanges_ccs(self, monkeypatch):
        monkeypatch.setattr(api, "getString", Mock(return_value="https://cci-api-eu.kia.com"))
        refresh_response = Mock(status_code=200)
        refresh_response.json.return_value = {
            "accessToken": "new-cci-access", "refreshToken": "new-cci-refresh", "nonCcsToken": "new-ncs",
        }
        monkeypatch.setattr(api.requests, "post", Mock(return_value=refresh_response))
        monkeypatch.setattr(api, "exchangeCcsToken", Mock(return_value="new-ccs-token"))

        result = api.refreshCciToken(self._token(), "kia")

        assert result["cciAccessToken"] == "new-cci-access"
        assert result["accessToken"] == "new-ccs-token"
        assert result["tokenType"] == "Bearer"


class TestGetAuthCode:
    def test_waf_abuse_block_raises(self, monkeypatch):
        monkeypatch.setattr(api, "getString", Mock(return_value="x"))
        fake_session = Mock()
        fake_session.get.return_value = Mock(
            text="Bad Request. It was classified as an abusing request and blocked.",
            url="https://idpconnect-eu.kia.com/error?status=400")
        monkeypatch.setattr(api.requests, "Session", Mock(return_value=fake_session))
        with pytest.raises(RuntimeError):
            api.getAuthCode("user@example.com", "pw", "kia", {})


class TestRequestToken:
    def test_populates_ccs_and_cci_fields(self, monkeypatch):
        monkeypatch.setattr(api, "getDeviceId", Mock(return_value={
            "deviceId": "dev-1", "gcmClientId": "c", "gcmVehicleId": "v"}))
        monkeypatch.setattr(api, "getAuthCode", Mock(return_value="auth-code-1"))
        monkeypatch.setattr(api, "exchangeCciToken", Mock(return_value={
            "cciAccessToken": "cci-access", "cciRefreshToken": "cci-refresh",
            "nonCcsToken": "ncs", "exchangeableAccessToken": "ex-access",
            "exchangeableRefreshToken": "ex-refresh", "nonCcsRefreshToken": "ncs-refresh",
            "idToken": "id-1",
        }))
        monkeypatch.setattr(api, "exchangeCcsToken", Mock(return_value="ccs-token-value"))
        monkeypatch.setattr(api, "registerDevice", Mock())

        token = api.requestToken("user@example.com", "pw", "kia")

        assert token["accessToken"] == "ccs-token-value"
        assert token["tokenType"] == "Bearer"
        assert token["refreshToken"] == "cci-refresh"
        assert token["cciAccessToken"] == "cci-access"


class TestRefreshToken:
    def test_delegates_to_refresh_cci_token(self, monkeypatch):
        refresh_mock = Mock(return_value={"accessToken": "new-ccs"})
        monkeypatch.setattr(api, "refreshCciToken", refresh_mock)
        token = {"cciAccessToken": "old"}

        result = api.refreshToken(token, "kia")

        refresh_mock.assert_called_once_with(token, "kia")
        assert result == {"accessToken": "new-ccs"}
