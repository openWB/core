"""Behaviour that was audited against the PHP implementation (see COMPATIBILITY.md)."""
import importlib
import logging
import threading
import urllib.request
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from src.authenticator import AuthConfig, Authenticator
from src.broker_access import BrokerAccess
from src.http_server import SimpleAPIServer
from src.parameter_handler import (
    ParameterHandler, READ_PARAMETER_ORDER, ReadView, auto_id, dispatch_read, discover_ids, format_raw_output,
    get_type_from_parameter, list_components, php_echo, _as_float, _opt_float)


@pytest.fixture(scope="module")
def simpleapi():
    with patch("logging.handlers.RotatingFileHandler", lambda *args, **kwargs: logging.NullHandler()):
        return importlib.import_module("simpleapi")


class Daemon:
    _normalize_io_output_type = staticmethod(lambda output_type: None)

    def _get_io_output_map(self, io_id, output_type):
        value = self.raw_value_cache.get(f"openWB/io/states/{io_id}/get/{output_type}")
        return value if isinstance(value, dict) else {}

    def __init__(self, cache=None):
        self.raw_value_cache = dict(cache or {})
        self.charge_template_cache = {}
        self.total_sums = {}
        self.primary_ids = {}
        self.lowest_ids = {}
        self.all_ids = {}


# ---- which parameter belongs to which component type (PHP: getTypeFromParameter) ----

def php_type_from_parameter(param):
    if 'chargepoint' in param or 'get_chargepoint' in param:
        return 'chargepoint'
    if param == 'get_io_input_all':
        return 'io_input'
    for needle, type_ in (('io', 'io'), ('battery', 'bat'), ('pv', 'pv'), ('counter', 'counter'),
                          ('consumer', 'consumer')):
        if needle in param:
            return type_
    return 'chargepoint'


@pytest.mark.parametrize("param", [p for p in READ_PARAMETER_ORDER if p != 'get_home_consumption'])
def test_component_type_of_every_read_parameter_matches_php(param):
    assert get_type_from_parameter(param) == php_type_from_parameter(param)


# ---- which components exist (PHP scanned one marker topic per component type) ----

CACHE = {
    'openWB/chargepoint/3/get/imported': 10.5,
    'openWB/chargepoint/5/get/imported': None,           # "null"
    'openWB/chargepoint/7/get/imported': '',              # empty
    'openWB/chargepoint/8/get/imported': True,            # not a number
    'openWB/chargepoint/9/config': {'name': 'no data yet'},
    'openWB/chargepoint/4/get/imported': 0,
    'openWB/bat/2/get/imported': 1.0,
    'openWB/pv/1/get/exported': 2.0,
    'openWB/pv/6/get/imported': 2.0,                      # the pv marker is "exported"
    'openWB/counter/0/get/imported': 3.0,
    'openWB/consumer/6/module': {'type': 'x'},
    'openWB/consumer/7/get/power': 5,                     # no module topic
    'openWB/io/states/2/get/digital_output': {},
    'openWB/io/states/4/get/analog_input': {'AI1': 1.0},
}


def test_only_components_with_a_value_in_their_marker_topic_are_known():
    daemon = Daemon(CACHE)

    assert discover_ids(daemon, 'chargepoint') == [3, 4]
    assert list_components(daemon) == {
        'chargepoint': [3, 4], 'battery': [2], 'pv': [1], 'counter': [0], 'consumer': [6], 'io': [2]}
    assert discover_ids(daemon, 'io_input') == [4]


def test_auto_id_is_the_lowest_known_one_or_the_grid_counter():
    daemon = Daemon({**CACHE, 'openWB/counter/2/get/imported': 1.0})

    assert auto_id(daemon, 'chargepoint') == 3
    assert auto_id(daemon, 'counter') == 0
    daemon.primary_ids['counter'] = 2
    assert auto_id(daemon, 'counter') == 2
    assert auto_id(Daemon(), 'chargepoint') is None


def test_ids_are_found_through_the_read_view_used_for_the_permission_check():
    view = ReadView(Daemon(CACHE))

    assert auto_id(view, 'bat') == 2
    assert list_components(view)['pv'] == [1]


def test_auto_id_for_io_inputs_includes_devices_without_outputs():
    result, _ = dispatch_read(ParameterHandler(Daemon(CACHE)), {'get_io_input_all': 'auto'}, {}, False)

    assert list(result) == ['io_4']


# ---- numbers ----

@pytest.mark.parametrize("value", [float('nan'), float('inf'), float('-inf')])
def test_non_finite_numbers_become_the_default_like_phps_floatval(value):
    assert _as_float(value) == 0.0
    assert _as_float(value, 50.0) == 50.0
    assert _opt_float(value) is None


@pytest.mark.parametrize("max_price, expected", [
    (None, 0.0), (0.0001, 10.0), (0.00007, 7.000000000000001), (0.0000123456, 1.2000000000000002)])
def test_max_price_eco_is_rounded_to_six_decimals_before_the_conversion(max_price, expected):
    daemon = Daemon({'openWB/chargepoint/3/get/imported': 1})
    eco = {} if max_price is None else {'max_price': max_price}
    daemon.charge_template_cache['3'] = {'chargemode': {'eco_charging': eco}}

    result, _ = dispatch_read(ParameterHandler(daemon), {'get_chargepoint_all': '3'}, {}, False)

    assert result['chargepoint_3']['max_price_eco'] == pytest.approx(expected, rel=1e-12)


# ---- raw output: what PHP's echo printed ----

@pytest.mark.parametrize("value, expected", [
    (1500.0, '1500'), (12.5, '12.5'), (231.54000854492188, '231.54000854492'), (1e25, '1.0E+25'),
    (0.00001, '1.0E-5'), (1.5e-7, '1.5E-7'), (-0.0, '-0'), (100000.0, '100000'), (1e15, '1.0E+15'),
    (7, '7'), (True, '1'), (False, ''), (None, ''), ('text', 'text'), ([1], 'Array'), ({}, 'Array')])
def test_php_echo(value, expected):
    assert php_echo(value) == expected


def test_raw_output_of_an_empty_result_is_empty():
    assert php_echo(format_raw_output({}, 'get_counter_power')) == ''


# ---- HTTP surface ----

@pytest.fixture
def server(simpleapi):
    daemon = simpleapi.SimpleMQTTDaemon.__new__(simpleapi.SimpleMQTTDaemon)
    daemon.lowest_ids, daemon.all_ids, daemon.total_sums, daemon.primary_ids = {}, {}, {}, {}
    daemon.raw_value_cache = {'openWB/counter/0/get/imported': 1.0, 'openWB/counter/0/get/power': 1500.0,
                              'openWB/counter/0/get/voltages': [231.54000854492188, 230.0, 229.5]}
    daemon.charge_template_cache = {}
    daemon.user_management_active = False
    daemon._request_publisher = threading.local()
    config = {'auth': {'enabled': False}, 'api': {}}
    authenticator = Authenticator(AuthConfig.from_dict(config['auth']), lambda user, password: True)
    http_server = SimpleAPIServer(('127.0.0.1', 0), daemon, ParameterHandler(daemon), authenticator,
                                  BrokerAccess(), config)
    threading.Thread(target=http_server.serve_forever, daemon=True).start()
    yield http_server
    http_server.shutdown()
    http_server.server_close()


def request(server, query, method='GET'):
    url = f"http://127.0.0.1:{server.server_address[1]}/?{query}"
    with urllib.request.urlopen(urllib.request.Request(url, method=method)) as response:
        return response.status, response.read().decode(), dict(response.headers)


def test_raw_number_is_printed_like_php(server):
    assert request(server, "get_counter_power=auto&raw=true")[:2] == (200, '1500')
    assert request(server, "get_counter_voltage_p1=auto&raw=true")[:2] == (200, '231.54000854492')


def test_raw_output_without_a_known_component_is_empty(server):
    assert request(server, "get_pv_power=auto&raw=true")[:2] == (200, '')


def test_list_components_lists_every_type(server):
    status, body, _ = request(server, "list_components=1")

    assert status == 200
    assert body == '{"chargepoint": [], "battery": [], "pv": [], "counter": [0], "consumer": [], "io": []}'


def test_head_request_answers_like_get_without_a_body(server):
    status, body, headers = request(server, "get_counter_power=auto", method='HEAD')

    assert (status, body) == (200, '')
    assert int(headers['Content-Length']) > 0


# ---- IO outputs ----

@pytest.fixture
def io_daemon(simpleapi):
    daemon = simpleapi.SimpleMQTTDaemon.__new__(simpleapi.SimpleMQTTDaemon)
    daemon.raw_value_cache = {}
    daemon._request_publisher = threading.local()
    daemon.client = SimpleNamespace(published=[], publish=lambda *args, **kwargs: None)
    daemon.published = []
    daemon._publish = lambda topic, payload: daemon.published.append((topic, payload))
    return daemon


@pytest.mark.parametrize("value, output_type, expected", [
    ('5', 'analog', '5'), ('2.5', 'analog', '2.5'), (' 7 ', 'analog', '7'), ('true', 'analog', '1'),
    ('off', 'analog', '0'), ('1e3', 'analog', '1000'), ('1', 'digital', 'true'), ('0', 'digital', 'false'),
    ('on', 'digital', 'true')])
def test_io_output_payloads(io_daemon, value, output_type, expected):
    assert io_daemon._set_io_output('1', value, 'X1', output_type)[0] is True

    assert io_daemon.published[-1][1] == expected


@pytest.mark.parametrize("value, output_type", [
    ('abc', 'analog'), ('nan', 'analog'), ('inf', 'analog'), ('1_0', 'analog'), ('2', 'digital'), ('abc', 'digital')])
def test_io_output_refuses_values_that_are_no_number_or_boolean(io_daemon, value, output_type):
    assert io_daemon._set_io_output('1', value, 'X1', output_type)[0] is False
    assert io_daemon.published == []


def test_responses_are_not_cacheable_like_the_php_ones_were(server):
    _, _, headers = request(server, "get_counter_power=auto")

    assert headers['Cache-Control'] == 'no-cache, no-store, must-revalidate'
    assert (headers['Pragma'], headers['Expires']) == ('no-cache', '0')


# ---- numbers in the published template ----

@pytest.mark.parametrize("number, expected", [(10.0, 10), (6.5, 6.5), (0.0, 0), (1e20, 1e20), (-3.0, -3)])
def test_whole_numbers_are_published_as_integers(number, expected):
    from src.parameter_handler import _whole_as_int
    result = _whole_as_int(number)

    assert result == expected and type(result) is type(expected)


def test_debug_info_names_the_credentials_and_the_failed_auto_id(server):
    plain = request(server, "get_pv_power=auto&debug=true")[1]
    with_login = request(server, "get_counter_power=auto&debug=true&username=u&password=p")[1]

    assert plain.startswith('{"debug_info": ["No credentials provided via parameters, using config or anonymous '
                            'access", "Auto-ID failed for get_pv_power: No pv devices found via MQTT wildcard scan"]')
    assert '"Using MQTT credentials from parameters: username=u"' in with_login


# ---- chargepoint array reads without a topic answer with nothing (like PHP) ----

@pytest.mark.parametrize("param", ['get_chargepoint_voltages', 'get_chargepoint_voltage_p2',
                                   'get_chargepoint_currents', 'get_chargepoint_current_p3',
                                   'get_chargepoint_powers'])
def test_chargepoint_array_reads_without_a_topic_return_nothing(param):
    daemon = Daemon({'openWB/chargepoint/3/get/imported': 1.0, 'openWB/chargepoint/3/get/voltages': None})

    missing, _ = dispatch_read(ParameterHandler(daemon), {param: '5'}, {}, False)

    assert missing == {}


def test_a_null_payload_is_no_missing_topic():
    daemon = Daemon({'openWB/chargepoint/3/get/voltages': None})

    result, _ = dispatch_read(ParameterHandler(daemon), {'get_chargepoint_voltages': '3'}, {}, False)

    assert result == {'chargepoint_3': {'voltages': [0.0, 0.0, 0.0]}}
