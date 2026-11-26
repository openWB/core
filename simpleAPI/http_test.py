import importlib
import logging
import threading
import urllib.error
import urllib.request
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from src.authenticator import AuthConfig, Authenticator
from src.broker_access import BrokerAccess
from src.http_server import SimpleAPIServer
from src.parameter_handler import ParameterHandler

LIVE_VALUES = '{"time": "12:00", "pv": [1, 2.5], "name": "a/b \\"q\\""}'


@pytest.fixture(scope="module")
def simpleapi():
    with patch("logging.handlers.RotatingFileHandler", lambda *args, **kwargs: logging.NullHandler()):
        return importlib.import_module("simpleapi")


@pytest.fixture
def daemon(simpleapi):
    daemon = simpleapi.SimpleMQTTDaemon.__new__(simpleapi.SimpleMQTTDaemon)
    daemon.lowest_ids, daemon.all_ids, daemon.total_sums = {}, {}, {}
    daemon.primary_ids, daemon.value_cache = {}, {}
    daemon.raw_value_cache, daemon.charge_template_cache = {}, {}
    daemon.user_management_active = False
    daemon._request_publisher = threading.local()
    return daemon


@pytest.fixture
def server(daemon):
    config = {'auth': {'enabled': False}, 'api': {}}
    authenticator = Authenticator(AuthConfig.from_dict(config['auth']), lambda user, password: True)
    http_server = SimpleAPIServer(('127.0.0.1', 0), daemon, ParameterHandler(daemon), authenticator,
                                  BrokerAccess(), config)
    thread = threading.Thread(target=http_server.serve_forever, daemon=True)
    thread.start()
    yield http_server
    http_server.shutdown()
    http_server.server_close()


def get(server, query, headers=None):
    url = f"http://127.0.0.1:{server.server_address[1]}/?{query}"
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=headers or {})) as response:
            return response.status, response.read().decode()
    except urllib.error.HTTPError as error:
        return error.code, error.read().decode()


def test_live_values_topic_is_kept_as_the_unparsed_string(daemon):
    daemon.client = SimpleNamespace()
    message = SimpleNamespace(topic="openWB/graph/lastlivevaluesJson", payload=LIVE_VALUES.encode())

    daemon._on_message(daemon.client, None, message)

    assert daemon.raw_value_cache["openWB/graph/lastlivevaluesJson"] == LIVE_VALUES


@pytest.mark.parametrize("query", ["get_lastlivevaluesjson=1", "get_lastlivevaluesjson=1&raw=true"])
def test_get_lastlivevaluesjson_returns_the_stored_json_unchanged(server, daemon, query):
    daemon.raw_value_cache["openWB/graph/lastlivevaluesJson"] = LIVE_VALUES

    assert get(server, query) == (200, LIVE_VALUES)


def test_get_lastlivevaluesjson_is_a_recognized_parameter_without_data(server):
    status, _ = get(server, "get_lastlivevaluesjson=1")

    assert status == 200


# ---- HTTPS detection behind the Apache proxy ----

@pytest.fixture
def https_only_server(daemon):
    config = {'auth': {'enabled': True, 'require_https': True, 'users': {'user': 'secret'}}, 'api': {}}
    authenticator = Authenticator(AuthConfig.from_dict(config['auth']), lambda user, password: False)
    http_server = SimpleAPIServer(('127.0.0.1', 0), daemon, ParameterHandler(daemon), authenticator,
                                  BrokerAccess(), config)
    threading.Thread(target=http_server.serve_forever, daemon=True).start()
    yield http_server
    http_server.shutdown()
    http_server.server_close()


QUERY = "get_lastlivevaluesjson=1&username=user&password=secret"


def test_credentials_work_when_the_proxy_reports_https(https_only_server, daemon):
    daemon.raw_value_cache["openWB/graph/lastlivevaluesJson"] = "{}"

    assert get(https_only_server, QUERY, {'X-Forwarded-Proto': 'https'}) == (200, "{}")


@pytest.mark.parametrize("headers", [{}, {'X-Forwarded-Proto': 'http'}])
def test_credentials_are_refused_over_plain_http(https_only_server, headers):
    status, _ = get(https_only_server, QUERY, headers)

    assert status == 401


def test_https_header_is_ignored_unless_it_comes_from_the_local_proxy():
    from src.http_server import SimpleAPIRequestHandler
    request = SimpleNamespace(headers={'X-Forwarded-Proto': 'https'})

    request.client_address = ('127.0.0.1', 4000)
    assert SimpleAPIRequestHandler._is_https(request) is True
    request.client_address = ('192.168.1.20', 4000)
    assert SimpleAPIRequestHandler._is_https(request) is False


# ---- the configuration with credentials is not served by the web server ----

def test_configuration_lives_outside_of_the_web_root(simpleapi):
    from pathlib import Path
    web_root = Path(simpleapi.__file__).resolve().parents[1]

    assert not Path(simpleapi.CONFIG_FILE_PATH).resolve().is_relative_to(web_root)


def test_default_configuration_is_used_until_the_home_file_exists(simpleapi, tmp_path):
    default = tmp_path / "default.json"
    default.write_text("{}")

    assert simpleapi.select_config_file(str(tmp_path / "missing.json"), str(default)) == str(default)
    assert simpleapi.select_config_file(str(default), "unused") == str(default)


def test_default_configuration_in_the_repository_holds_no_credentials():
    import json
    from pathlib import Path
    config = json.loads((Path(__file__).resolve().parents[1] / "data/config/simpleapi_config.json").read_text())

    assert config['auth']['tokens'] == [] and config['auth']['users'] == {}
    assert config['username'] is None and config['password'] is None


def test_htaccess_blocks_the_configuration_file_as_a_second_layer():
    from pathlib import Path
    htaccess = (Path(__file__).resolve().parents[1] / ".htaccess").read_text()

    assert r"RedirectMatch 404 /simpleapi_config\.json$" in htaccess


def test_missing_bcrypt_backend_refuses_the_login_instead_of_failing_the_request():
    from passlib.exc import MissingBackendError
    authenticator = Authenticator(AuthConfig.from_dict({'users': {'user': '$2b$12$' + 'a' * 53}}), lambda u, p: False)

    with patch("src.authenticator.bcrypt.verify", side_effect=MissingBackendError("no backends available")):
        assert authenticator.authenticate({'username': 'user', 'password': 'x'}, None, False) is None
