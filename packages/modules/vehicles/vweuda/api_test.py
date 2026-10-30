import io
import json
import zipfile
from unittest.mock import Mock
from urllib.parse import parse_qs

import pytest
from modules.common.req import get_http_session

from modules.vehicles.vweuda import api


UNIVERSAL_FORM = ('<form method="post" {action}><input name="state" value="flow-state">'
                  '<input name="username"><input name="password" type="password"></form>')


@pytest.mark.parametrize("action", ["", 'action="/u/login/password?state=flow-state"'])
def test_universal_login_posts_once_preserves_state_and_stops_at_callback(requests_mock, action):
    signin = "https://identity.vwgroup.io/u/login?state=flow-state"
    post_url = signin if not action else "https://identity.vwgroup.io/u/login/password?state=flow-state"
    callback = api.BASE_URL + api.CALLBACK_LOGIN_PATH + "?code=secret"
    requests_mock.get(api.OIDC_AUTHORIZE_URL, status_code=302, headers={"Location": signin})
    requests_mock.get(signin, text=UNIVERSAL_FORM.format(action=action))
    credentials = requests_mock.post(post_url, status_code=302, headers={"Location": callback})
    requests_mock.get(callback, status_code=302, headers={
        "Location": api.BASE_URL + "/missing-cms-page", "Set-Cookie": "access_token=token; Path=/; Secure",
    })
    with get_http_session() as session:
        client = api.EudaApiClient(session, "test@example.com", "password", brand="cupra")
        client.login()
        assert client._logged_in
    assert len([request for request in requests_mock.request_history if request.method == "POST"]) == 1
    assert credentials.last_request.qs == {"state": ["flow-state"]}
    assert credentials.last_request.headers["Referer"] == signin
    assert parse_qs(credentials.last_request.text) == {
        "state": ["flow-state"], "username": ["test@example.com"], "password": ["password"], "action": ["default"],
    }
    assert requests_mock.request_history[-1].url == callback


@pytest.mark.parametrize("status", [200, 400])
def test_universal_login_rejected_credentials_do_not_succeed(requests_mock, status):
    signin = "https://identity.vwgroup.io/u/login?state=flow-state"
    form = UNIVERSAL_FORM.format(action="")
    requests_mock.get(api.OIDC_AUTHORIZE_URL, status_code=302, headers={"Location": signin})
    requests_mock.get(signin, text=form)
    requests_mock.post(signin, status_code=status, text=form)
    with get_http_session() as session:
        client = api.EudaApiClient(session, "test@example.com", "wrong-password", brand="cupra")
        with pytest.raises(api.AuthError, match="check email and password"):
            client.login()
        assert not client._logged_in


@pytest.mark.parametrize("status", [429, 503])
def test_universal_login_transient_post_error_remains_retryable(requests_mock, status):
    signin = "https://identity.vwgroup.io/u/login?state=flow-state"
    requests_mock.get(api.OIDC_AUTHORIZE_URL, status_code=302, headers={"Location": signin})
    requests_mock.get(signin, text=UNIVERSAL_FORM.format(action=""))
    requests_mock.post(signin, status_code=status)
    with get_http_session() as session:
        client = api.EudaApiClient(session, "test@example.com", "password", brand="cupra")
        with pytest.raises(api.ApiError) as error:
            client.login()
        assert not isinstance(error.value, api.AuthError)
        assert error.value.status == status
        assert not client._logged_in


def test_incomplete_login_form_is_not_accepted(requests_mock):
    requests_mock.get(api.OIDC_AUTHORIZE_URL, text='<form><input name="state" value="s"></form>')
    with get_http_session() as session:
        with pytest.raises(api.AuthError, match="Could not parse identity login form"):
            api.EudaApiClient(session, "test@example.com", "password").login()


def test_login_stops_at_callback_and_posts_relay_state(requests_mock):
    signin = "https://identity.vwgroup.io/signin-service/login"
    authenticate = signin + "/authenticate"
    callback = api.BASE_URL + api.CALLBACK_LOGIN_PATH + "?code=secret"
    cms = api.BASE_URL + "/missing-cms-page"
    form = '<form action="/signin-service/login"><input name="hmac" value="h"></form>'
    form += '<script>csrf_token: "csrf"</script>'
    requests_mock.get(api.OIDC_AUTHORIZE_URL, status_code=302, headers={"Location": signin})
    requests_mock.get(signin, text=form)
    password_page = '<script>templateModel: {"hmac":"h2","relayState":"relay"}; csrf_token: "csrf2"</script>'
    requests_mock.post(signin, status_code=302, headers={"Location": authenticate + "?relayState=relay"})
    requests_mock.get(authenticate, text=password_page)
    credentials = requests_mock.post(authenticate, status_code=302, headers={"Location": callback})
    requests_mock.get(callback, status_code=302, headers={
        "Location": cms, "Set-Cookie": "access_token=token; Path=/; Secure",
    })
    with get_http_session() as session:
        client = api.EudaApiClient(session, "test@example.com", "password")
        client.login()
        assert client._logged_in
    assert all(request.url != cms for request in requests_mock.request_history)
    assert credentials.last_request.query == ""
    fields = parse_qs(credentials.last_request.text)
    assert fields["password"] == ["password"]
    assert fields["relayState"] == ["relay"]


def test_callback_without_cookie_is_not_successful(requests_mock, monkeypatch):
    callback = api.BASE_URL + api.CALLBACK_LOGIN_PATH
    with get_http_session() as session:
        client = api.EudaApiClient(session, "test@example.com", "password")
        form = '<form><input name="hmac" value="h"></form><script>csrf_token: "csrf"</script>'
        requests_mock.get(api.OIDC_AUTHORIZE_URL, text=form)
        requests_mock.post(api.OIDC_AUTHORIZE_URL, text=form)
        requests_mock.get(callback, status_code=302)
        monkeypatch.setattr(client, "_post_login_form", lambda *args, **kwargs: session.get(callback))
        with pytest.raises(api.AuthError, match="cookie missing"):
            client.login()
        assert not client._logged_in


@pytest.mark.parametrize("status", [404, 429, 500, 503])
def test_transient_login_errors_remain_retryable(requests_mock, status):
    requests_mock.get(api.OIDC_AUTHORIZE_URL, status_code=status)
    with get_http_session() as session:
        with pytest.raises(api.ApiError) as error:
            api.EudaApiClient(session, "test@example.com", "password").login()
        assert not isinstance(error.value, api.AuthError)
        assert error.value.status == status


def test_json_session_expiry_retries_only_once(requests_mock, monkeypatch):
    url = api.BASE_URL + "/test-json"
    response = requests_mock.get(url, [{"status_code": 401}, {"status_code": 403}])
    with get_http_session() as session:
        client = api.EudaApiClient(session, "test@example.com", "password")
        client._logged_in = True
        login = Mock()
        monkeypatch.setattr(client, "login", login)
        with pytest.raises(api.ApiError) as error:
            client._get_json(url)
        assert error.value.status == 403
        login.assert_called_once()
        assert response.call_count == 2


def test_helper_http_error_preserves_login_error_body(requests_mock):
    requests_mock.get(api.OIDC_AUTHORIZE_URL, status_code=400,
                      text='<script>templateModel: {"error": {"text": "Account locked"}}</script>')
    with get_http_session() as session:
        with pytest.raises(api.AuthError, match="Account locked"):
            api.EudaApiClient(session, "test@example.com", "password").login()


def test_download_session_expiry_preserves_zip_decoding(requests_mock, monkeypatch):
    payload = {"vin": "WVW00000000000001", "Data": []}
    archive = io.BytesIO()
    with zipfile.ZipFile(archive, "w") as handle:
        handle.writestr("data.json", json.dumps(payload))
    url = api.BASE_URL + api.DOWNLOAD_PATH.format(vin=payload["vin"], identifier="id")
    requests_mock.get(url, [{"status_code": 401}, {"content": archive.getvalue()}])
    with get_http_session() as session:
        client = api.EudaApiClient(session, "test@example.com", "password")
        client._logged_in = True
        login = Mock()
        monkeypatch.setattr(client, "login", login)
        name, data = client.download_dataset(payload["vin"], "id", "data.zip")
        assert name == "data.json"
        assert data == payload
        login.assert_called_once()
