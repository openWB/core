import threading
import time
from unittest.mock import Mock

import pytest

from modules.vehicles.byd import api
from modules.vehicles.byd.config import BydConfiguration


@pytest.fixture(autouse=True)
def _clear_caches():
    api._session_cache.clear()
    api._login_failure_cache.clear()
    api._fingerprint_cache.clear()
    api._account_locks.clear()
    api._guest_vins.clear()
    api._user_type_settled.clear()
    yield


def _config(username="user@example.com", vin="VIN123") -> BydConfiguration:
    return BydConfiguration(username=username, password="pw", vin=vin)


def test_fetch_soc_requires_vin():
    with pytest.raises(api.BydApiError, match="VIN"):
        api.fetch_soc(_config(vin=""), 1)


def test_fetch_soc_requires_credentials():
    with pytest.raises(api.BydApiError, match="Benutzername"):
        api.fetch_soc(BydConfiguration(username="", password="", vin="VIN123"), 1)


class TestResolveAccountFingerprint:
    def test_same_account_reuses_fingerprint(self):
        first = api.resolve_account_fingerprint("acc1", "")
        second = api.resolve_account_fingerprint("acc1", "")
        assert first == second

    def test_different_accounts_get_different_fingerprints(self):
        first = api.resolve_account_fingerprint("acc1", "")
        second = api.resolve_account_fingerprint("acc2", "")
        assert first != second

    def test_adopts_already_persisted_fingerprint(self):
        result = api.resolve_account_fingerprint("acc1", '{"imei": "already-persisted"}')
        assert result == '{"imei": "already-persisted"}'


class TestGetSession:
    def test_cached_session_is_reused(self, monkeypatch):
        login_mock = Mock(return_value={"user_id": "u", "sign_token": "s",
                                        "encry_token": "e", "created_at": time.monotonic()})
        monkeypatch.setattr(api, "_login", login_mock)

        api._get_session(_config())
        api._get_session(_config())

        login_mock.assert_called_once()

    def test_failed_login_blocks_retries_during_cooldown(self, monkeypatch):
        monkeypatch.setattr(api, "_login", Mock(side_effect=api.BydAuthenticationError("bad credentials")))

        with pytest.raises(api.BydAuthenticationError, match="bad credentials"):
            api._get_session(_config())
        with pytest.raises(api.BydAuthenticationError, match="wird für weitere"):
            api._get_session(_config())

    def test_concurrent_logins_for_same_account_only_login_once(self, monkeypatch):
        call_count = 0

        def slow_login(config):
            nonlocal call_count
            call_count += 1
            time.sleep(0.05)
            return {"user_id": "u", "sign_token": "s", "encry_token": "e", "created_at": time.monotonic()}

        monkeypatch.setattr(api, "_login", slow_login)

        threads = [threading.Thread(target=api._get_session, args=(_config(),)) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert call_count == 1

    def test_force_relogin_reuses_session_already_refreshed_by_another_vehicle(self, monkeypatch):
        rejected_session = {"user_id": "u", "sign_token": "old", "encry_token": "old",
                            "created_at": time.monotonic()}
        refreshed_session = {"user_id": "u", "sign_token": "new", "encry_token": "new",
                             "created_at": time.monotonic()}
        api._session_cache["user@example.com"] = refreshed_session
        login_mock = Mock(return_value={"user_id": "u", "sign_token": "newer", "encry_token": "newer",
                                        "created_at": time.monotonic()})
        monkeypatch.setattr(api, "_login", login_mock)

        result = api._get_session(_config(), force_relogin=True, rejected_session=rejected_session)

        assert result is refreshed_session
        login_mock.assert_not_called()

    def test_force_relogin_logs_in_when_cached_session_is_still_the_rejected_one(self, monkeypatch):
        rejected_session = {"user_id": "u", "sign_token": "old", "encry_token": "old",
                            "created_at": time.monotonic()}
        api._session_cache["user@example.com"] = rejected_session
        new_session = {"user_id": "u", "sign_token": "new", "encry_token": "new",
                       "created_at": time.monotonic()}
        monkeypatch.setattr(api, "_login", Mock(return_value=new_session))

        result = api._get_session(_config(), force_relogin=True, rejected_session=rejected_session)

        assert result is new_session


class TestFetchRealtimeAuthError:
    def test_auth_error_during_poll_is_not_swallowed(self, monkeypatch):
        monkeypatch.setattr(api, "_inner_base", Mock(return_value={}))
        monkeypatch.setattr(api, "_post_token_json", Mock(side_effect=[
            {},  # trigger response, not yet ready
            api.BydAuthenticationError("session expired"),
        ]))

        with pytest.raises(api.BydAuthenticationError, match="session expired"):
            api._fetch_realtime(_config(), {"user_id": "u", "sign_token": "s", "encry_token": "e"})

    def test_other_api_errors_are_retried(self, monkeypatch):
        monkeypatch.setattr(api, "_inner_base", Mock(return_value={}))
        responses = [{}, api.BydApiError("transient"), {"onlineState": 1, "time": 123}]
        monkeypatch.setattr(api, "_post_token_json", Mock(side_effect=responses))
        monkeypatch.setattr(api.time, "sleep", Mock())

        result = api._fetch_realtime(_config(), {"user_id": "u", "sign_token": "s", "encry_token": "e"})

        assert result == {"onlineState": 1, "time": 123}


SESSION = {"user_id": "u", "sign_token": "s", "encry_token": "e"}


class TestUserTypeEnvelope:
    def _post(self, monkeypatch, user_type):
        post_secure = Mock(return_value={"code": "0"})
        monkeypatch.setattr(api, "_post_secure", post_secure)
        signed_fields = {}
        real_build_sign_string = api.crypto.build_sign_string

        def capture(fields, key):
            signed_fields.update(fields)
            return real_build_sign_string(fields, key)

        monkeypatch.setattr(api.crypto, "build_sign_string", capture)
        api._post_token_json("/x", _config(), SESSION, {"vin": "VIN123"}, user_type)
        return post_secure.call_args.args[1], signed_fields

    def test_owner_envelope_has_no_user_type(self, monkeypatch):
        outer, signed = self._post(monkeypatch, None)

        assert "userType" not in outer
        assert "userType" not in signed

    def test_guest_envelope_sends_user_type_and_signs_it(self, monkeypatch):
        outer, signed = self._post(monkeypatch, api.USER_TYPE_GUEST)

        assert outer["userType"] == "1"
        assert signed["userType"] == "1"


class TestPostVehicleJson:
    @staticmethod
    def _error(code):
        return api.BydApiError(f"code={code}", code)

    @staticmethod
    def _user_types(post_mock):
        return [call.args[4] for call in post_mock.call_args_list]

    def test_owner_is_asked_without_user_type_once(self, monkeypatch):
        post = Mock(return_value={"ok": 1})
        monkeypatch.setattr(api, "_post_token_json", post)

        assert api._post_vehicle_json("/x", _config(), SESSION, {"vin": "VIN123"}) == {"ok": 1}

        assert self._user_types(post) == [None]

    def test_guest_is_detected_from_1001_and_remembered(self, monkeypatch):
        post = Mock(side_effect=[self._error("1001"), {"ok": 1}, {"ok": 2}])
        monkeypatch.setattr(api, "_post_token_json", post)
        inner = {"vin": "VIN123", "random": "A", "timeStamp": "1"}

        assert api._post_vehicle_json("/x", _config(), SESSION, inner) == {"ok": 1}
        assert api._post_vehicle_json("/x", _config(), SESSION, inner) == {"ok": 2}

        assert self._user_types(post) == [None, "1", "1"]

    def test_retry_uses_fresh_random_and_timestamp(self, monkeypatch):
        post = Mock(side_effect=[self._error("1001"), {}])
        monkeypatch.setattr(api, "_post_token_json", post)
        inner = {"vin": "VIN123", "random": "A", "timeStamp": "1"}

        api._post_vehicle_json("/x", _config(), SESSION, inner)

        first, retry = (call.args[3] for call in post.call_args_list)
        assert first == inner
        assert retry["random"] != "A" and retry["timeStamp"] != "1"
        assert retry["vin"] == "VIN123"

    def test_owner_wrongly_assumed_as_guest_is_corrected_by_8003(self, monkeypatch):
        api._guest_vins[("user@example.com", "VIN123")] = True
        post = Mock(side_effect=[self._error("8003"), {"ok": 1}])
        monkeypatch.setattr(api, "_post_token_json", post)

        api._post_vehicle_json("/x", _config(), SESSION, {"vin": "VIN123"})

        assert self._user_types(post) == ["1", None]
        assert api._guest_vins[("user@example.com", "VIN123")] is False

    def test_refused_both_ways_raises_first_error_and_is_not_asked_twice_again(self, monkeypatch):
        post = Mock(side_effect=[self._error("1001"), self._error("8003"), self._error("1001")])
        monkeypatch.setattr(api, "_post_token_json", post)

        with pytest.raises(api.BydApiError) as first:
            api._post_vehicle_json("/x", _config(), SESSION, {"vin": "VIN123"})
        with pytest.raises(api.BydApiError):
            api._post_vehicle_json("/x", _config(), SESSION, {"vin": "VIN123"})

        assert first.value.code == "1001"
        assert self._user_types(post) == [None, "1", None]
        assert ("user@example.com", "VIN123") not in api._guest_vins

    def test_other_answer_to_the_retry_still_corrects_the_guess(self, monkeypatch):
        post = Mock(side_effect=[self._error("1001"), self._error("6002")])
        monkeypatch.setattr(api, "_post_token_json", post)

        with pytest.raises(api.BydApiError) as error:
            api._post_vehicle_json("/x", _config(), SESSION, {"vin": "VIN123"})

        assert error.value.code == "6002"
        assert api._guest_vins[("user@example.com", "VIN123")] is True

    def test_other_errors_are_not_retried(self, monkeypatch):
        post = Mock(side_effect=self._error("6002"))
        monkeypatch.setattr(api, "_post_token_json", post)

        with pytest.raises(api.BydApiError):
            api._post_vehicle_json("/x", _config(), SESSION, {"vin": "VIN123"})

        post.assert_called_once()

    def test_session_expiry_is_passed_through_without_retry(self, monkeypatch):
        post = Mock(side_effect=api.BydAuthenticationError("session expired"))
        monkeypatch.setattr(api, "_post_token_json", post)

        with pytest.raises(api.BydAuthenticationError):
            api._post_vehicle_json("/x", _config(), SESSION, {"vin": "VIN123"})

        post.assert_called_once()
