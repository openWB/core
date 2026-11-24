import importlib
import logging
from unittest.mock import patch

import pytest

from src.parameter_handler import ParameterHandler, dispatch_read, READ_DISPATCH, READ_PARAMETER_ORDER


@pytest.fixture(scope="module")
def simpleapi():
    with patch("logging.handlers.RotatingFileHandler", lambda *args, **kwargs: logging.NullHandler()):
        return importlib.import_module("simpleapi")


class FakeDaemon:
    def __init__(self):
        self.raw_value_cache = {
            "openWB/counter/set/home_consumption": 850.5,
            "openWB/counter/set/daily_yield_home_consumption": 4200,
            "openWB/counter/set/imported_home_consumption": 123456.7,
            "openWB/consumer/6/get/temperatures": [45.5, None, 20],
            "openWB/consumer/6/get/set_power": 1500,
            "openWB/consumer/6/get/state": True,
            "openWB/consumer/6/get/plug_state": False,
            "openWB/consumer/6/get/rfid": "tag1",
            "openWB/consumer/6/get/rfid_timestamp": 1700000000,
            "openWB/bat/2/get/state_str": "Steuerung aktiv",
            "openWB/bat/2/get/max_charge_power": 5000,
            "openWB/bat/2/get/max_discharge_power": 4000,
            "openWB/counter/15/get/local_power": 321.0,
        }
        self.charge_template_cache = {}
        self.lowest_ids = {'consumer': 6, 'bat': 2, 'counter': 15}
        self.all_ids = {}
        self.total_sums = {}


def read(params):
    result, _ = dispatch_read(ParameterHandler(FakeDaemon()), params, {}, False)
    return result


def test_home_consumption_ignores_the_id_and_is_not_mistaken_for_an_io_parameter():
    assert read({'get_home_consumption': 'auto'}) == {
        'home_consumption': {'power': 850.5, 'daily_imported': 4200.0, 'imported': 123456.7}}


def test_consumer_values():
    result = read({'get_consumer_all': 'auto'})['consumer_6']

    assert result['temperatures'] == [45.5, None, 20.0]
    assert (result['set_power'], result['state'], result['plug_state']) == (1500.0, True, False)
    assert (result['rfid'], result['rfid_timestamp']) == ('tag1', 1700000000)
    assert read({'get_consumer_temperatures': '6'}) == {'consumer_6': {'temperatures': [45.5, None, 20.0]}}
    assert read({'get_consumer_set_power': '7'}) == {'consumer_7': {'set_power': None}}


def test_battery_and_counter_values():
    assert read({'get_battery_state_str': 'auto'}) == {'battery_2': {'state_str': 'Steuerung aktiv'}}
    battery = read({'get_battery': 'auto'})['battery_2']
    assert (battery['max_charge_power'], battery['max_discharge_power']) == (5000.0, 4000.0)
    assert read({'get_counter_local_power': 'auto'}) == {'counter_15': {'local_power': 321.0}}
    assert read({'get_counter': 'auto'})['counter_15']['local_power'] == 321.0


def test_every_whitelisted_parameter_has_a_handler():
    assert [p for p in READ_PARAMETER_ORDER if p not in READ_DISPATCH] == []


def make_daemon(simpleapi):
    daemon = simpleapi.SimpleMQTTDaemon.__new__(simpleapi.SimpleMQTTDaemon)
    daemon.lowest_ids, daemon.all_ids, daemon.primary_ids = {}, {}, {}
    daemon.raw_value_cache = {}
    daemon.published = []
    daemon._transform_and_publish = lambda topic, value: daemon.published.append(topic)
    return daemon


def test_grid_counter_is_the_primary_counter_even_without_the_lowest_id(simpleapi):
    daemon = make_daemon(simpleapi)
    daemon._register_component_id('counter', 0)
    daemon._register_component_id('counter', 3)
    daemon.raw_value_cache["openWB/counter/3/get/power"] = 100

    daemon._update_grid_counter([{'id': 3, 'type': 'counter', 'children': []}])
    daemon._register_component_id('counter', 0)

    assert daemon.lowest_ids['counter'] == 3
    assert daemon.published == ["openWB/counter/3/get/power"]


def test_hierarchy_without_a_grid_counter_changes_nothing(simpleapi):
    daemon = make_daemon(simpleapi)
    daemon._register_component_id('counter', 0)

    daemon._update_grid_counter([{'id': 4, 'type': 'inverter', 'children': []}])

    assert daemon.lowest_ids['counter'] == 0


def make_io_daemon(simpleapi):
    daemon = make_daemon(simpleapi)
    daemon.lowest_ids['io'] = 1
    daemon.calls = []
    daemon._set_io_output = lambda *args: daemon.calls.append(args) or (True, "ok")
    return daemon


@pytest.mark.parametrize("topic_parts, expected", [
    (['io', '2', 'digital_output', 'DO1'], ('2', '1', 'DO1', 'digital_output')),
    (['io', '2', 'DO1'], ('2', '1', 'DO1', None)),
    (['io', 'analog', 'AO1'], ('1', '1', 'AO1', 'analog')),
    (['io', 'DO1'], ('1', '1', 'DO1', None)),
])
def test_io_set_topic(simpleapi, topic_parts, expected):
    daemon = make_io_daemon(simpleapi)

    assert daemon._handle_io_operation(topic_parts, '1') is True
    assert daemon.calls == [(expected[0], '1', expected[2], expected[3])]


def test_io_set_topic_needs_an_output_name(simpleapi):
    daemon = make_io_daemon(simpleapi)

    assert daemon._handle_io_operation(['io', '2'], '1') is False
    assert daemon.calls == []


def test_vehicle_and_manual_soc_have_mqtt_set_topics(simpleapi):
    daemon = make_daemon(simpleapi)
    calls = []
    daemon._set_vehicle = lambda cp, value: calls.append(('vehicle', cp, value)) or (True, "ok")
    daemon._set_manual_soc = lambda cp, value: calls.append(('manual_soc', cp, value)) or (True, "ok")

    assert daemon._handle_chargepoint_operation(['chargepoint', '3', 'vehicle'], '2') is True
    assert daemon._handle_chargepoint_operation(['chargepoint', '3', 'manual_soc'], '55') is True
    assert calls == [('vehicle', '3', '2'), ('manual_soc', '3', '55')]
