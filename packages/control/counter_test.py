from dataclasses import dataclass
from typing import List, Optional
from unittest.mock import Mock
import pytest

from helpermodules import timecheck
from control import counter as counter_module
from control import data
from control.chargepoint.chargepoint import Chargepoint
from control.consumer.consumer import Consumer
from control.counter import Counter, CounterData, Get
from control.ev.ev import Ev
from control.ev.charge_template import ChargeTemplate
from control.general import General
from control.chargepoint.chargepoint_state import ChargepointState
from helpermodules import timecheck
from modules.common.fault_state import FaultStateLevel


@pytest.fixture
def general_data_fixture() -> None:
    data.data_init(Mock())
    data.data.general_data = General()


@pytest.mark.parametrize("fault_state, expected_loadmanagement_available",
                         [pytest.param(FaultStateLevel.ERROR, 1652683252),
                          pytest.param(FaultStateLevel.NO_ERROR, None)])
def test_set_loadmanagement_state(fault_state: FaultStateLevel,
                                  expected_loadmanagement_available: bool,
                                  monkeypatch,
                                  data_):
    # setup
    connected_cps_mock = Mock(return_value=["cp3", "cp4"])
    monkeypatch.setattr(data.data.counter_all_data, "get_loads_of_counter", connected_cps_mock)
    id_mock = Mock(return_value=0)
    monkeypatch.setattr(data.data.counter_all_data, "get_id_evu_counter", id_mock)
    name_mock = Mock(return_value="Test")
    monkeypatch.setattr(counter_module, "get_component_name_by_id", name_mock)
    counter = Counter(0)
    counter.data.get.fault_state = fault_state

    # execution
    counter._get_loadmanagement_state()

    # evaluation
    assert counter.data.set.error_timer == expected_loadmanagement_available


def test_get_loadmanagement_state_within_grace_period_stays_available(monkeypatch, data_):
    # setup
    connected_cps_mock = Mock(return_value=["cp3", "cp4"])
    monkeypatch.setattr(data.data.counter_all_data, "get_loads_of_counter", connected_cps_mock)
    counter = Counter(0)
    counter.data.get.fault_state = FaultStateLevel.ERROR
    counter.data.set.error_timer = timecheck.create_timestamp()

    # execution
    loadmanagement_available = counter._get_loadmanagement_state()

    # evaluation
    assert loadmanagement_available is True


@pytest.mark.parametrize("raw_currents_left, expected_max_exceeding",
                         [pytest.param([32, 32, 15], [0]*3, id="not exceeded"),
                          pytest.param([32, 35, 18], [0]*3, id="not exceeded with export"),
                          pytest.param([38, 55, 39], [0]*3, id="not exceeded with export two phases"),
                          pytest.param([32, 32, 13], [0, 0, 1], id="exceeded on one phase"),
                          pytest.param([29, 11, 8], [0, 0, 3], id="exceeded on two phases"),
                          pytest.param([35, 11, 8], [0, 6, 9], id="exceeded on two phases with export")])
def test_get_unbalanced_load_exceeding(raw_currents_left: List[float],
                                       expected_max_exceeding: List[float],
                                       monkeypatch,
                                       general_data_fixture):
    # setup
    get_evu_counter_mock = Mock(return_value="counter0")
    monkeypatch.setattr(data.data.counter_all_data, "get_evu_counter_str", get_evu_counter_mock)
    counter = Counter(0)
    counter.data.config.max_currents = [32]*3
    data.data.general_data.data.chargemode_config.unbalanced_load = True

    # execution
    max_exceeding = counter.get_unbalanced_load_exceeding(raw_currents_left)

    # evaluation
    assert max_exceeding == expected_max_exceeding


@pytest.mark.parametrize("loadmanagement_available, max_currents, expected_raw_currents_left",
                         [pytest.param(True, [40]*3, [40, 0, 10], id="Überbelastung"),
                          pytest.param(True, [60]*3, [60, 15, 30]),
                          pytest.param(False, [40]*3, [10.1449275362318853]*3, id="Kein Lastmanagement")])
def test_set_current_left(loadmanagement_available: bool,
                          max_currents: List[float],
                          expected_raw_currents_left: List[float],
                          monkeypatch,
                          data_):
    # setup
    get_loads_of_counter_mock = Mock(return_value=["cp3", "cp4", "cp5"])
    monkeypatch.setattr(data.data.counter_all_data, "get_loads_of_counter", get_loads_of_counter_mock)
    counter = Counter(0)
    counter.data.config.max_currents = max_currents
    counter.data.config.max_total_power = sum(max_currents)*230
    counter.data.config.max_power_errorcase = 7000
    counter.data.get.currents = [55]*3

    # execution
    counter._set_current_left(loadmanagement_available)

    # evaluation
    assert counter.data.set.raw_currents_left == expected_raw_currents_left


def test_set_power_left_excludes_consumer_power_after_60s(monkeypatch, data_):
    # setup
    get_evu_counter_str_mock = Mock(return_value="counter0")
    monkeypatch.setattr(data.data.counter_all_data, "get_evu_counter_str", get_evu_counter_str_mock)
    counter = Counter(0)
    counter.data.config.max_total_power = 24000
    counter.data.get.power = 1000
    data.data.cp_data = {}
    data.data.consumer_data = {"consumer1": Consumer(1)}
    data.data.consumer_data["consumer1"].data.get.power = 2000
    data.data.consumer_data["consumer1"].data.get.fault_state = FaultStateLevel.ERROR
    data.data.consumer_data["consumer1"].data.set.error_timer = timecheck.create_timestamp() - 61
    data.data.consumer_data["consumer1"].data.set.switch_interval_elapsed = True

    # execution
    counter._set_power_left(True)

    # evaluation
    # power_raw = 1000 - 0 (kein Verbraucher wird nach 60s Fehler mehr abgezogen) -> raw_power_left = 24000 - 1000
    assert counter.data.set.raw_power_left == 23000


@dataclass
class Params:
    name: str
    feed_in_limit: bool
    reserved_surplus: float
    surplus: float
    threshold: float
    timestamp_switch_on_off: Optional[str]
    state: ChargepointState
    expected_msg: Optional[str]
    expected_timestamp_switch_on_off: Optional[str]
    expected_reserved_surplus: float


cases = [
    Params("Einschaltschwelle wurde unterschritten, Timer zurücksetzen", False, 1500, -119,
           1500, 1652683250.0, ChargepointState.SWITCH_ON_DELAY,
           Counter.SWITCH_ON_TEXTS_CP.fallen_below.format(1500), None, 0),
    Params("Timer starten", False, 0, 1501, 1500, None, ChargepointState.NO_CHARGING_ALLOWED,
           Counter.SWITCH_ON_TEXTS_CP.waiting.format("30 Sek."), 1652683252.0, 1500),
    Params("Einschaltschwelle nicht erreicht", False, 0, 1499, 1500,
           None, ChargepointState.NO_CHARGING_ALLOWED, Counter.SWITCH_ON_TEXTS_CP.not_exceeded, None, 0),
    Params("Einschaltschwelle läuft", False, 1500, 121, 1500,
           1652683250.0, ChargepointState.SWITCH_ON_DELAY, None, 1652683250.0, 1500),
    Params("Feed_in_limit, Einschaltschwelle wurde unterschritten, Timer zurücksetzen", True, 1500,
           -681, 15000, 1652683250.0, ChargepointState.SWITCH_ON_DELAY,
           Counter.SWITCH_ON_TEXTS_CP.fallen_below.format(1500), None, 0),
    Params("Feed_in_limit, Timer starten", True, 0, 15001, 15000, None, ChargepointState.NO_CHARGING_ALLOWED,
           Counter.SWITCH_ON_TEXTS_CP.waiting.format("30 Sek.")+" Die Einspeisegrenze wird berücksichtigt.",
           1652683252.0, 1500),
    Params("Feed_in_limit, Einschaltschwelle nicht erreicht", True, 0, 14999,
           15000, None, ChargepointState.NO_CHARGING_ALLOWED,
           Counter.SWITCH_ON_TEXTS_CP.not_exceeded.format(1500), None, 0),
    Params("Feed_in_limit, Einschaltschwelle läuft", True, 1500, 15001,
           15000, 1652683250.0, ChargepointState.SWITCH_ON_DELAY, None, 1652683250.0, 1500),
]


@pytest.mark.parametrize("params", cases, ids=[c.name for c in cases])
def test_switch_on_threshold_reached(params: Params, caplog, general_data_fixture, monkeypatch):
    # setup
    c = Counter(0)
    c.data.set.reserved_surplus = params.reserved_surplus
    cp = Chargepoint(0, None)
    ev = Ev(0)
    cp.data.control_parameter.phases = 1
    cp.data.control_parameter.state = params.state
    cp.data.control_parameter.timestamp_switch_on_off = params.timestamp_switch_on_off
    ev.data.charge_template = ChargeTemplate()
    data.data.general_data.data.chargemode_config.surplus.feed_in_limit = params.feed_in_limit
    cp.data.set.charging_ev_data = ev
    mock_calc_switch_on_power = Mock(return_value=[params.surplus, params.threshold])
    monkeypatch.setattr(Counter, "calc_switch_on_power", mock_calc_switch_on_power)

    # execution
    c.switch_on_threshold_reached(cp)

    # evaluation
    assert c.data.set.reserved_surplus == params.expected_reserved_surplus
    assert cp.data.get.state_str is None or cp.data.get.state_str == params.expected_msg
    assert (cp.data.control_parameter.timestamp_switch_on_off ==
            params.expected_timestamp_switch_on_off)


@pytest.mark.parametrize("control_range, evu_power, expected_range_offset",
                         [pytest.param([0, 230], 200, 115, id="Bezug, im Regelbereich"),
                          pytest.param([0, 230], 290, 115, id="Bezug, über Regelbereich"),
                          pytest.param([0, 230], -100, 115, id="Bezug, unter Regelbereich"),
                          pytest.param([-230, 0], -104, -115, id="Einspeisung, im Regelbereich"),
                          pytest.param([-230, 0], 80, -115, id="Einspeisung, über Regelbereich"),
                          pytest.param([-230, 0], -300, -115, id="Einspeisung, unter Regelbereich"),
                          ],
                         )
def test_control_range(control_range, evu_power, expected_range_offset, general_data_fixture, monkeypatch):
    # setup
    get_evu_counter_mock = Mock(return_value=Mock(spec=Counter, data=Mock(
        spec=CounterData, get=Mock(spec=Get, power=evu_power))))
    monkeypatch.setattr(data.data.counter_all_data, "get_evu_counter", get_evu_counter_mock)
    data.data.general_data.data.chargemode_config.surplus.control_range = control_range
    c = Counter(0)

    # execution
    range_offset = c._control_range_offset()

    # evaluation
    assert range_offset == expected_range_offset


@pytest.mark.parametrize("load_factory, expected",
                         [pytest.param(lambda: Chargepoint(0, None), -200, id="Ladepunkt"),
                          pytest.param(lambda: Consumer(0), -50, id="Verbraucher")])
def test_calc_switch_off_threshold_by_load(load_factory, expected: float, general_data_fixture):
    # setup
    surplus_config = data.data.general_data.data.chargemode_config.surplus
    surplus_config.feed_in_limit = False
    surplus_config.vehicle.switch_off_threshold = -200
    surplus_config.consumer.switch_off_threshold = -50
    c = Counter(0)

    # execution
    threshold = c.calc_switch_off_threshold(load_factory())

    # evaluation
    assert threshold == expected


def test_reset_switch_on_off_ignores_stale_timestamp_without_delay_state(general_data_fixture, monkeypatch):
    # setup
    evu_counter = Counter(0)
    evu_counter.data.set.reserved_surplus = 690
    monkeypatch.setattr(data.data.counter_all_data, "get_evu_counter", Mock(return_value=evu_counter))

    consumer = Consumer(7)
    consumer.data.control_parameter.timestamp_switch_on_off = 1652683250.0
    consumer.data.control_parameter.state = ChargepointState.NO_CHARGING_ALLOWED
    consumer.data.control_parameter.required_current = 21.70138888888889
    consumer.data.control_parameter.phases = 1
    consumer.data.get.charge_state = False

    # execution
    evu_counter.reset_switch_on_off(consumer)

    # evaluation
    assert evu_counter.data.set.reserved_surplus == 690
    assert consumer.data.control_parameter.timestamp_switch_on_off is None
    assert consumer.data.control_parameter.state == ChargepointState.NO_CHARGING_ALLOWED


def test_reset_switch_on_off_releases_reserved_surplus_on_switch_on_delay(general_data_fixture, monkeypatch):
    # setup
    evu_counter = Counter(0)
    evu_counter.data.set.reserved_surplus = 690
    monkeypatch.setattr(data.data.counter_all_data, "get_evu_counter", Mock(return_value=evu_counter))

    consumer = Consumer(6)
    consumer.data.control_parameter.timestamp_switch_on_off = 1652683250.0
    consumer.data.control_parameter.state = ChargepointState.SWITCH_ON_DELAY
    consumer.data.control_parameter.required_current = 3
    consumer.data.control_parameter.phases = 1
    consumer.data.get.charge_state = False

    # execution
    evu_counter.reset_switch_on_off(consumer)

    # evaluation
    assert evu_counter.data.set.reserved_surplus == 0
    assert consumer.data.control_parameter.timestamp_switch_on_off is None
    assert consumer.data.control_parameter.state == ChargepointState.NO_CHARGING_ALLOWED
