import io
import json
import zipfile
from unittest.mock import Mock
from urllib.parse import parse_qs

import pytest
from modules.common.req import get_http_session

from modules.vehicles.vweuda import api


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
