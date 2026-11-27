import copy
import importlib
import json
import logging
import threading
from types import SimpleNamespace
from unittest.mock import patch

import paho.mqtt.client as mqtt
import pytest

from src.parameter_handler import ParameterHandler, dispatch_write


@pytest.fixture(scope="module")
def simpleapi():
    with patch("logging.handlers.RotatingFileHandler", lambda *args, **kwargs: logging.NullHandler()):
        return importlib.import_module("simpleapi")


TEMPLATE = {
    'chargemode': {
        'selected': 'instant_charging',
        'instant_charging': {'current': 16, 'limit': {'selected': 'none', 'amount': 10000, 'soc': 80}},
        'pv_charging': {'min_current': 6, 'min_soc': 0, 'limit': {'selected': 'none', 'amount': 5000, 'soc': 90}},
        'eco_charging': {'max_price': 0.0001},
    }
}


class Recorder:
    def __init__(self, rc=mqtt.MQTT_ERR_SUCCESS):
        self.published = []
        self.rc = rc

    def publish(self, topic, payload, qos=0, retain=False):
        self.published.append((topic, payload))
        return SimpleNamespace(rc=self.rc)


class Session:
    """Stands in for UserSession: records publishes, or fails them."""

    def __init__(self, error=None):
        self.error = error
        self.published = []

    def publish(self, topic, payload, retain=True):
        if self.error:
            raise self.error
        self.published.append((topic, payload))


@pytest.fixture
def daemon(simpleapi):
    daemon = simpleapi.SimpleMQTTDaemon.__new__(simpleapi.SimpleMQTTDaemon)
    daemon.lowest_ids, daemon.all_ids, daemon.primary_ids = {'chargepoint': 3}, {}, {}
    daemon.raw_value_cache = {'openWB/chargepoint/3/get/imported': 5.0}
    daemon.charge_template_cache = {'3': copy.deepcopy(TEMPLATE)}
    daemon._request_publisher = threading.local()
    daemon.client = Recorder()
    return daemon


def write(daemon, params, all_params=None):
    return dispatch_write(ParameterHandler(daemon), params, all_params or {})


def published_template(daemon):
    topic, payload = daemon.client.published[-1]
    assert topic == "openWB/set/chargepoint/3/set/charge_template"
    return json.loads(payload)


@pytest.mark.parametrize("all_params", [{}, {'chargepoint_nr': 'auto'}, {'chargepoint_nr': ''},
                                        {'chargepoint_nr': '3'}])
@pytest.mark.parametrize("params, check", [
    ({'set_chargemode': 'pv'}, lambda t: t['chargemode']['selected'] == 'pv_charging'),
    ({'chargecurrent': '10'}, lambda t: t['chargemode']['instant_charging']['current'] == 10),
    ({'minimal_pv_soc': '30'}, lambda t: t['chargemode']['pv_charging']['min_soc'] == 30),
    ({'instant_charging_limit': 'soc'}, lambda t: t['chargemode']['instant_charging']['limit']['selected'] == 'soc'),
])
def test_template_writes_work_with_explicit_automatic_and_missing_chargepoint_id(daemon, all_params, params, check):
    result = write(daemon, params, all_params)

    assert result['success'] is True, result
    assert check(published_template(daemon))


def test_refused_write_leaves_the_cached_template_untouched(daemon):
    with daemon.http_write(Session(PermissionError("Not authorized to publish"))):
        result = write(daemon, {'set_chargemode': 'pv'}, {'chargepoint_nr': '3'})

    assert result == {'success': False, 'message': 'Not authorized to publish'}
    assert daemon.charge_template_cache['3'] == TEMPLATE


@pytest.mark.parametrize("params", [{'set_chargemode': 'pv'}, {'instant_charging_limit': 'soc'},
                                    {'instant_charging_soc': '50'}])
def test_next_permitted_write_does_not_carry_a_refused_change(daemon, params):
    with daemon.http_write(Session(PermissionError("Not authorized to publish"))):
        write(daemon, params, {'chargepoint_nr': '3'})

    session = Session()
    with daemon.http_write(session):
        assert write(daemon, {'chargecurrent': '10'}, {'chargepoint_nr': '3'})['success'] is True

    expected = copy.deepcopy(TEMPLATE)
    expected['chargemode']['instant_charging']['current'] = 10
    assert json.loads(session.published[-1][1]) == expected


@pytest.mark.parametrize("error", [TimeoutError("Publish was not acknowledged by the broker"),
                                   ConnectionError("connection lost")])
def test_failed_transfer_is_reported_as_failure(daemon, error):
    with daemon.http_write(Session(error)):
        result = write(daemon, {'set_chargemode': 'pv'}, {'chargepoint_nr': '3'})

    assert result['success'] is False
    assert str(error) in result['message']
    assert daemon.charge_template_cache['3'] == TEMPLATE


def test_failed_publish_of_the_daemon_connection_is_reported_as_failure(daemon):
    daemon.client = Recorder(rc=mqtt.MQTT_ERR_NO_CONN)

    result = write(daemon, {'set_chargemode': 'pv'}, {'chargepoint_nr': '3'})

    assert result['success'] is False
    assert 'failed' in result['message']


# ---- HTTP value contract of the PHP API (floatval/intval, no new limits) ----

def published_value(daemon, *path):
    value = published_template(daemon)
    for step in path:
        value = value[step]
    return value


@pytest.mark.parametrize("param, path", [
    ('chargecurrent', ('chargemode', 'instant_charging', 'current')),
    ('minimal_permanent_current', ('chargemode', 'pv_charging', 'min_current')),
])
@pytest.mark.parametrize("value, expected", [('6.5', 6.5), ('10', 10.0), ('16', 16.0), (' 8 ', 8.0), ('1e1', 10.0)])
def test_currents_accept_decimals_like_phps_floatval(daemon, param, path, value, expected):
    assert write(daemon, {param: value}, {'chargepoint_nr': '3'})['success'] is True

    assert published_value(daemon, *path) == expected


@pytest.mark.parametrize("param, path", [
    ('instant_charging_amount', ('chargemode', 'instant_charging', 'limit', 'amount')),
    ('pv_charging_amount', ('chargemode', 'pv_charging', 'limit', 'amount')),
])
@pytest.mark.parametrize("value, expected_wh", [('0', 0), ('12.5', 12500), ('75', 75000), ('10', 10000),
                                                ('0.0015', 1)])
def test_amounts_are_non_negative_decimal_kwh_converted_to_wh(daemon, param, path, value, expected_wh):
    assert write(daemon, {param: value}, {'chargepoint_nr': '3'})['success'] is True

    assert published_value(daemon, *path) == expected_wh


@pytest.mark.parametrize("param", ['instant_charging_amount', 'pv_charging_amount'])
def test_negative_amount_is_refused(daemon, param):
    result = write(daemon, {param: '-1'}, {'chargepoint_nr': '3'})

    assert result == {'success': False, 'message': 'Amount must be >= 0'}
    assert daemon.client.published == []


@pytest.mark.parametrize("param, path", [
    ('minimal_pv_soc', ('chargemode', 'pv_charging', 'min_soc')),
    ('instant_charging_soc', ('chargemode', 'instant_charging', 'limit', 'soc')),
    ('pv_charging_soc', ('chargemode', 'pv_charging', 'limit', 'soc')),
])
@pytest.mark.parametrize("value, expected", [('30', 30), ('55.9', 55), (' 7', 7)])
def test_soc_values_use_phps_intval(daemon, param, path, value, expected):
    assert write(daemon, {param: value}, {'chargepoint_nr': '3'})['success'] is True

    assert published_value(daemon, *path) == expected


@pytest.mark.parametrize("param", ['instant_charging_soc', 'pv_charging_soc'])
def test_soc_out_of_range_is_refused(daemon, param):
    result = write(daemon, {param: '101'}, {'chargepoint_nr': '3'})

    assert result == {'success': False, 'message': 'SoC must be between 0 and 100'}


def test_missing_charge_template_section_gives_the_php_error(daemon):
    del daemon.charge_template_cache['3']['chargemode']['pv_charging']

    assert write(daemon, {'minimal_pv_soc': '30'}, {'chargepoint_nr': '3'}) == {
        'success': False, 'message': 'Invalid charge template format or missing pv_charging'}


def test_unknown_chargepoint_template_gives_the_php_error(daemon):
    assert write(daemon, {'chargecurrent': '10'}, {'chargepoint_nr': '9'}) == {
        'success': False,
        'message': 'Error setting chargecurrent: No data received for topic: openWB/chargepoint/9/set/charge_template'}


# ---- HTTP writes are not retained (the PHP API published without -r); the MQTT set topics still are ----

class RetainRecorder(Recorder):
    def publish(self, topic, payload, qos=0, retain=False):
        self.published.append((topic, payload, retain))
        return SimpleNamespace(rc=mqtt.MQTT_ERR_SUCCESS)


def test_http_write_through_the_daemon_connection_is_not_retained(daemon):
    daemon.client = RetainRecorder()

    with daemon.http_write():
        assert write(daemon, {'set_chargemode': 'pv', 'bat_mode': 'ev_mode'}, {'chargepoint_nr': '3'})['success']

    assert [retain for _, _, retain in daemon.client.published] == [False, False]


def test_http_write_through_a_user_session_is_not_retained(daemon):
    class RetainSession(Session):
        def publish(self, topic, payload, retain=True):
            self.published.append((topic, payload, retain))

    session = RetainSession()
    with daemon.http_write(session):
        assert write(daemon, {'chargecurrent': '10'}, {'chargepoint_nr': '3'})['success']

    assert [retain for _, _, retain in session.published] == [False]


def test_mqtt_set_topic_writes_stay_retained(daemon):
    daemon.client = RetainRecorder()

    assert daemon._handle_chargepoint_operation(['chargepoint', '3', 'chargecurrent'], '10') is True

    assert [retain for _, _, retain in daemon.client.published] == [True]


def test_retain_is_only_switched_off_inside_the_http_write(daemon):
    daemon.client = RetainRecorder()

    with daemon.http_write():
        pass
    daemon._publish("openWB/set/x", "1")

    assert daemon.client.published == [("openWB/set/x", "1", True)]


# ---- garbage is rejected (PHP turned it into 0 or a numeric prefix; documented in COMPATIBILITY.md) ----

@pytest.mark.parametrize("param", ['chargecurrent', 'minimal_permanent_current', 'minimal_pv_soc', 'max_price_eco',
                                   'instant_charging_amount', 'pv_charging_amount', 'instant_charging_soc',
                                   'pv_charging_soc', 'vehicle', 'manual_soc', 'bat_power_reserve'])
@pytest.mark.parametrize("value", ['abc', '', '7,5', '12abc', 'NaN', '--1', '1 2'])
def test_non_numeric_values_are_rejected_without_publishing(daemon, param, value):
    result = write(daemon, {param: value}, {'chargepoint_nr': '3'})

    assert result['success'] is False
    assert value in result['message'] or value == ''
    assert daemon.client.published == []


# ---- several template parameters in one request ----

def test_several_template_parameters_of_one_request_all_reach_the_template(daemon):
    with daemon.http_write():
        result = write(daemon, {'set_chargemode': 'pv', 'chargecurrent': '12', 'minimal_pv_soc': '40'},
                       {'chargepoint_nr': '3'})

    assert result['success'] is True
    template = published_template(daemon)['chargemode']
    assert (template['selected'], template['instant_charging']['current'], template['pv_charging']['min_soc']) == (
        'pv_charging', 12.0, 40)
    assert daemon.charge_template_cache['3'] == TEMPLATE


def test_the_next_request_starts_from_the_template_openwb_reported(daemon):
    with daemon.http_write():
        write(daemon, {'chargecurrent': '12'}, {'chargepoint_nr': '3'})
    with daemon.http_write():
        write(daemon, {'minimal_pv_soc': '40'}, {'chargepoint_nr': '3'})

    template = published_template(daemon)['chargemode']
    assert template['instant_charging']['current'] == 16
    assert template['pv_charging']['min_soc'] == 40


def test_whole_currents_reach_the_template_as_integers(daemon):
    with daemon.http_write():
        write(daemon, {'chargecurrent': '10', 'minimal_permanent_current': '6.5'}, {'chargepoint_nr': '3'})

    template = published_template(daemon)['chargemode']
    assert template['instant_charging']['current'] == 10 and isinstance(template['instant_charging']['current'], int)
    assert template['pv_charging']['min_current'] == 6.5
