import threading
import time
from unittest.mock import Mock

import pytest
from requests.exceptions import HTTPError

from modules.vehicles.saic_ismart import api
from modules.vehicles.saic_ismart.config import SaicIsmartConfiguration


@pytest.fixture(autouse=True)
def _clear_caches():
    api._session_cache.clear()
    api._account_locks.clear()
    yield


def _config(username="user@example.com", vin="VIN123") -> SaicIsmartConfiguration:
    return SaicIsmartConfiguration(username=username, password="pw", vin=vin)


def test_fetch_soc_requires_vin():
    with pytest.raises(api.SaicApiError, match="VIN"):
        api.fetch_soc(_config(vin=""))


def test_fetch_soc_requires_credentials():
    with pytest.raises(api.SaicApiError, match="Benutzername"):
        api.fetch_soc(SaicIsmartConfiguration(username="", password="", vin="VIN123"))


class TestGetSession:
    def test_cached_session_is_reused(self, monkeypatch):
        login_mock = Mock(return_value={"access_token": "t", "expires_at": time.monotonic() + 3600})
        monkeypatch.setattr(api, "_login", login_mock)

        api._get_session(_config())
        api._get_session(_config())

        login_mock.assert_called_once()

    def test_concurrent_logins_for_same_account_only_login_once(self, monkeypatch):
        call_count = 0

        def slow_login(config):
            nonlocal call_count
            call_count += 1
            time.sleep(0.05)
            return {"access_token": "t", "expires_at": time.monotonic() + 3600}

        monkeypatch.setattr(api, "_login", slow_login)

        threads = [threading.Thread(target=api._get_session, args=(_config(),)) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert call_count == 1


class TestCallWithRelogin:
    def test_success_on_first_try_does_not_relogin(self, monkeypatch):
        relogin_mock = Mock()
        monkeypatch.setattr(api, "_get_session", relogin_mock)

        result, token = api._call_with_relogin(_config(), "token-1", lambda t: f"ok-{t}")

        assert result == "ok-token-1"
        assert token == "token-1"
        relogin_mock.assert_not_called()

    def test_auth_error_triggers_one_relogin_and_retry(self, monkeypatch):
        monkeypatch.setattr(api, "_get_session", Mock(return_value="token-2"))
        action = Mock(side_effect=[api.SaicAuthenticationError("expired"), "ok"])

        result, token = api._call_with_relogin(_config(), "token-1", action)

        assert result == "ok"
        assert token == "token-2"
        assert action.call_args_list == [(("token-1",),), (("token-2",),)]


class TestFetchSocWakesAndRetriesWithinAuthScope:
    def test_wake_vehicle_auth_error_triggers_relogin(self, monkeypatch):
        monkeypatch.setattr(api, "_get_session", Mock(return_value="token-fresh"))
        monkeypatch.setattr(api, "_fetch_charging_mgmt_data", Mock(side_effect=[
            {"chrgMgmtData": {"bmsPackSOCDsp": api.SOC_INVALID_SENTINEL}},
            {"chrgMgmtData": {"bmsPackSOCDsp": 555}},
        ]))
        wake_mock = Mock(side_effect=[api.SaicAuthenticationError("expired"), None])
        monkeypatch.setattr(api, "_wake_vehicle", wake_mock)

        result = api.fetch_soc(_config())

        assert result.soc == 55.5
        assert wake_mock.call_count == 2


class TestSendHttpLevelAuthError:
    def test_http_401_raises_authentication_error_not_http_error(self, monkeypatch):
        # Die Cloud lehnt eine ungueltige Session manchmal schon auf HTTP-Ebene ab (zB nach
        # Login in der iSMART-App auf dem Handy), nicht nur ueber das eigene code-Feld in einer
        # 200-Antwort - muss als SaicAuthenticationError erkannt werden, damit der automatische
        # Relogin in _call_with_relogin() greift (siehe Discussion zu wiederholtem 401 ohne Relogin).
        response = Mock(status_code=401, headers={})
        response.raise_for_status = Mock(side_effect=HTTPError("401 Client Error"))
        session = Mock()
        session.request = Mock(return_value=response)
        monkeypatch.setattr(api.req, "get_http_session", Mock(return_value=session))

        with pytest.raises(api.SaicAuthenticationError):
            api._send("GET", "/vehicle/charging/mgmtData?vin=xxx", _config(), "token")
