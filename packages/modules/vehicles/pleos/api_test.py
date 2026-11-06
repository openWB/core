import time
from unittest.mock import Mock

from modules.vehicles.pleos import api
from modules.vehicles.pleos.config import PleosToken


def _session_returning(payload):
    session = Mock()
    response = Mock()
    response.json.return_value = payload
    session.get.return_value = response
    session.post.return_value = response
    return session


class TestValidateToken:
    def test_reuses_valid_token(self, monkeypatch):
        session = _session_returning({})
        monkeypatch.setattr(api.req, "get_http_session", lambda: session)
        token = PleosToken(access_token="cached", expires_in=3600, created_at=int(time.time()))

        result = api.validate_token("kia", "cid", "csec", token)

        assert result.access_token == "cached"
        session.post.assert_not_called()

    def test_requests_new_token_when_expired(self, monkeypatch):
        session = _session_returning({"data": {"accessToken": "fresh", "expiresIn": 3600}})
        monkeypatch.setattr(api.req, "get_http_session", lambda: session)
        token = PleosToken(access_token="old", expires_in=10, created_at=int(time.time()) - 100)

        result = api.validate_token("kia", "cid", "csec", token)

        assert result.access_token == "fresh"
        session.post.assert_called_once()

    def test_raises_when_no_access_token_in_response(self, monkeypatch):
        session = _session_returning({"data": {}})
        monkeypatch.setattr(api.req, "get_http_session", lambda: session)

        try:
            api.validate_token("kia", "cid", "csec", PleosToken())
            assert False, "expected Exception"
        except Exception:
            pass


class TestGetBattery:
    def test_returns_charge_data(self, monkeypatch):
        payload = {"data": {"charge": {"stateOfCharge": 72.5}}}
        session = _session_returning(payload)
        monkeypatch.setattr(api.req, "get_http_session", lambda: session)

        result = api.get_battery("kia", "VIN1", PleosToken(access_token="t"))

        assert result["charge"]["stateOfCharge"] == 72.5


class TestGetDistanceToEmptyKm:
    def test_converts_miles_to_km(self, monkeypatch):
        payload = {"data": {"distanceToEmpties": [{"type": "EV", "value": "100", "unit": "mile"}]}}
        session = _session_returning(payload)
        monkeypatch.setattr(api.req, "get_http_session", lambda: session)

        result = api.get_distance_to_empty_km("kia", "VIN1", PleosToken(access_token="t"))

        assert round(result, 2) == 160.93

    def test_ignores_non_ev_entries(self, monkeypatch):
        payload = {"data": {"distanceToEmpties": [{"type": "ICE", "value": "500", "unit": "km"}]}}
        session = _session_returning(payload)
        monkeypatch.setattr(api.req, "get_http_session", lambda: session)

        assert api.get_distance_to_empty_km("kia", "VIN1", PleosToken(access_token="t")) is None

    def test_returns_none_on_invalid_value(self, monkeypatch):
        payload = {"data": {"distanceToEmpties": [{"type": "EV", "value": "invalid", "unit": "km"}]}}
        session = _session_returning(payload)
        monkeypatch.setattr(api.req, "get_http_session", lambda: session)

        assert api.get_distance_to_empty_km("kia", "VIN1", PleosToken(access_token="t")) is None


class TestGetOdometerKm:
    def test_returns_value_in_km(self, monkeypatch):
        payload = {"data": {"odometer": {"value": "15234", "unit": "km"}}}
        session = _session_returning(payload)
        monkeypatch.setattr(api.req, "get_http_session", lambda: session)

        assert api.get_odometer_km("kia", "VIN1", PleosToken(access_token="t")) == 15234.0
