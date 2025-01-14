from typing import Dict, NamedTuple, Optional, Tuple
from unittest.mock import Mock

import pytest

from control import data
from control import optional
from control.ev.charge_template import SelectedPlan
from control.chargepoint.charging_type import ChargingType
from control.ev.ev import ChargeTemplate
from control.ev.ev_template import EvTemplate, EvTemplateData
from control.general import General
from helpermodules import timecheck
from helpermodules.abstract_plans import Limit, ScheduledChargingPlan, TimeChargingPlan


@pytest.fixture(autouse=True)
def data_module() -> None:
    data.data_init(Mock())
    data.data.general_data = General()
    data.data.optional_data = optional.Optional()


@pytest.mark.parametrize(
    "plans, soc, used_amount_time_charging, plan_found, expected",
    [
        pytest.param({}, 0, 0, None, (0, "stop", ChargeTemplate.TIME_CHARGING_NO_PLAN_CONFIGURED, None),
                     id="no plan defined"),
        pytest.param({"0": TimeChargingPlan(id=0)}, 0, 0,  None,
                     (0, "stop", ChargeTemplate.TIME_CHARGING_NO_PLAN_ACTIVE, None), id="no plan active"),
        pytest.param({"0": TimeChargingPlan(id=0)}, 0, 0,  TimeChargingPlan(id=0),
                     (16, "time_charging", None, 0), id="plan active"),
        pytest.param({"0": TimeChargingPlan(id=0, limit=Limit(selected="soc"))}, 100, 0,
                     TimeChargingPlan(id=0, limit=Limit(selected="soc")),
                     (0, "stop", ChargeTemplate.TIME_CHARGING_SOC_REACHED, 0),
                     id="plan active, soc is reached"),
        pytest.param({"0": TimeChargingPlan(id=0, limit=Limit(selected="soc"))}, 40, 0,
                     TimeChargingPlan(id=0, limit=Limit(selected="soc")),
                     (16, "time_charging", None, 0), id="plan active, soc is not reached"),
        pytest.param({"0": TimeChargingPlan(id=0, limit=Limit(selected="soc"))}, None, 0,
                     TimeChargingPlan(id=0, limit=Limit(selected="soc")),
                     (16, "time_charging", None, 0), id="plan active, soc is not defined"),
        pytest.param({"0": TimeChargingPlan(id=0, limit=Limit(selected="amount"))}, 0, 1500,
                     TimeChargingPlan(id=0, limit=Limit(selected="amount")),
                     (0, "stop", ChargeTemplate.TIME_CHARGING_AMOUNT_REACHED, 0),
                     id="plan active, used_amount_time_charging is reached"),
        pytest.param({"0": TimeChargingPlan(id=0, limit=Limit(selected="amount"))}, 0, 500,
                     TimeChargingPlan(id=0, limit=Limit(selected="amount")),
                     (16, "time_charging", None, 0),
                     id="plan active, used_amount_time_charging is not reached"),
        pytest.param({"0": TimeChargingPlan(id=0)}, 0, 0,  None,
                     (0, "stop", ChargeTemplate.TIME_CHARGING_NO_PLAN_ACTIVE, None), id="plan defined but not found"),
    ]
)
def test_time_charging(plans: Dict[int, TimeChargingPlan], soc: float, used_amount_time_charging: float,
                       plan_found: TimeChargingPlan,
                       expected: Tuple[int, str, Optional[str], Optional[str]],
                       monkeypatch):
    # setup
    ct = ChargeTemplate(0)
    ct.data.time_charging.plans = plans
    check_plans_timeframe_mock = Mock(return_value=plan_found)
    monkeypatch.setattr(timecheck, "check_plans_timeframe", check_plans_timeframe_mock)

    # execution
    ret = ct.time_charging(soc, used_amount_time_charging, ChargingType.AC.value)

    # evaluation
    assert ret == expected


@pytest.mark.parametrize(
    "selected, current_soc, used_amount, expected",
    [
        pytest.param("none", 0, 0, (10, "instant_charging", None), id="without limit"),
        pytest.param("soc", None, 0, (10, "instant_charging", None), id="limit soc: soc not defined"),
        pytest.param("soc", 49, 0, (10, "instant_charging", None), id="limit soc: soc not reached"),
        pytest.param("soc", 50, 0, (0, "stop", ChargeTemplate.INSTANT_CHARGING_SOC_REACHED),
                     id="limit soc: soc reached"),
        pytest.param("amount", 0, 999, (10, "instant_charging", None), id="limit amount: amount not reached"),
        pytest.param("amount", 0, 1000, (0, "stop", ChargeTemplate.INSTANT_CHARGING_AMOUNT_REACHED),
                     id="limit amount: amount reached"),
    ])
def test_instant_charging(selected: str, current_soc: float, used_amount: float,
                          expected: Tuple[int, str, Optional[str]]):
    # setup
    data.data.optional_data.data.et.active = False
    ct = ChargeTemplate(0)
    ct.data.chargemode.instant_charging.limit.selected = selected

    # execution
    ret = ct.instant_charging(current_soc, used_amount, ChargingType.AC.value)

    # evaluation
    assert ret == expected


@pytest.mark.parametrize(
    "min_soc, min_current, current_soc, expected",
    [
        pytest.param(0, 0, 100, (0, "stop", ChargeTemplate.PV_CHARGING_SOC_REACHED), id="max soc reached"),
        pytest.param(15, 0, 14, (10, "instant_charging", ChargeTemplate.PV_CHARGING_SOC_CHARGING),
                     id="min soc not reached"),
        pytest.param(15, 0, None, (6, "pv_charging", None), id="soc not defined"),
        pytest.param(15, 8, 15, (8, "instant_charging", ChargeTemplate.PV_CHARGING_MIN_CURRENT_CHARGING),
                     id="min current configured"),
        pytest.param(15, 0, 15, (6, "pv_charging", None), id="bare pv charging"),
    ])
def test_pv_charging(min_soc: int, min_current: int, current_soc: float,
                     expected: Tuple[int, str, Optional[str]]):
    # setup
    ct = ChargeTemplate(0)
    ct.data.chargemode.pv_charging.min_soc = min_soc
    ct.data.chargemode.pv_charging.min_current = min_current
    data.data.bat_all_data.data.config.configured = True

    # execution
    ret = ct.pv_charging(current_soc, 6, ChargingType.AC.value)

    # evaluation
    assert ret == expected


Params = NamedTuple("Params", [("name", str),
                               ("phase_switch_supported", bool),
                               ("chargemode_phases", int),
                               ("search_plan", Optional[SelectedPlan]),
                               ("expected_max_current", int),
                               ("phases", int),
                               ("max_phases", int),
                               ("expected_phases", int)])

cases = [
    Params(name="no phase switch, one phase", phase_switch_supported=False, chargemode_phases=0,
           search_plan=None, phases=1, max_phases=3, expected_max_current=32, expected_phases=1),
    Params(name="no phase switch, multi phase", phase_switch_supported=False, chargemode_phases=0,
           search_plan=None, phases=3, max_phases=3, expected_max_current=16, expected_phases=3),
    Params(name="no automatic mode, multi phase", phase_switch_supported=True, chargemode_phases=2,
           search_plan=None, phases=2, max_phases=2, expected_max_current=16, expected_phases=2),
    Params(name="select phases, not enough time", phase_switch_supported=True, chargemode_phases=0, search_plan=Mock(
        spec=SelectedPlan, remaining_time=300), phases=1, max_phases=3, expected_max_current=16, expected_phases=3),
    Params(name="select phases, enough time", phase_switch_supported=True, chargemode_phases=0, search_plan=Mock(
        spec=SelectedPlan, remaining_time=301), phases=1, max_phases=3, expected_max_current=32, expected_phases=1)
]


@pytest.mark.parametrize("params", cases, ids=[c.name for c in cases])
def test_scheduled_charging_recent_plan(params: Params, monkeypatch):
    # setup
    ct = ChargeTemplate(0)
    get_phases_chargemode_mock = Mock(return_value=params.chargemode_phases)
    monkeypatch.setattr(data.data.general_data, "get_phases_chargemode", get_phases_chargemode_mock)
    search_plan_mock = Mock(return_value=params.search_plan)
    monkeypatch.setattr(ChargeTemplate, "_search_plan", search_plan_mock)
    evt_data = Mock(spec=EvTemplateData, max_current_multi_phases=16, max_current_single_phase=32)
    evt = Mock(spec=EvTemplate, data=evt_data)

    # execution
    ct.scheduled_charging_recent_plan(50, evt, params.phases, 5, params.max_phases,
                                      params.phase_switch_supported, ChargingType.AC.value)

    # evaluation
    assert search_plan_mock.call_args.args[0] == params.expected_max_current
    assert search_plan_mock.call_args.args[3] == params.expected_phases


@pytest.mark.parametrize(
    "selected, phases, expected_duration, expected_missing_amount",
    [
        pytest.param("soc", 1, 10062.111801242236, 9000, id="soc, one phase"),
        pytest.param("amount", 2, 447.2049689440994, 800, id="amount, two phases"),
    ])
def test_calculate_duration(selected: str, phases: int, expected_duration: float, expected_missing_amount: float):
    # setup
    ct = ChargeTemplate(0)
    plan = ScheduledChargingPlan()
    plan.limit.selected = selected
    # execution
    duration, missing_amount = ct._calculate_duration(plan, 60, 45000, 200, phases, ChargingType.AC.value, EvTemplate())

    # evaluation
    assert duration == expected_duration
    assert missing_amount == expected_missing_amount


@pytest.mark.parametrize(
    "check_duration_return1, check_duration_return2, expected_plan_num",
    [
        pytest.param((-50, False), (60, False), 0, id="too late, but didn't miss date for today"),
        pytest.param((-50, True), (60, False), 1, id="too late and missed date for today"),
        pytest.param((-50, True), (-60, True), None, id="missed both"),
        pytest.param((50, False), (60, False), 0, id="in time, plan 1"),
        pytest.param((50, False), (40, False), 1, id="in time, plan 2"),
    ])
def test_search_plan(check_duration_return1: Tuple[Optional[float], bool],
                     check_duration_return2: Tuple[Optional[float], bool],
                     expected_plan_num: Optional[int],
                     monkeypatch):
    # setup
    calculate_duration_mock = Mock(return_value=(100, 200))
    monkeypatch.setattr(ChargeTemplate, "_calculate_duration", calculate_duration_mock)
    check_duration_mock = Mock(side_effect=[check_duration_return1, check_duration_return2])
    monkeypatch.setattr(timecheck, "check_duration", check_duration_mock)
    ct = ChargeTemplate(0)
    plan_mock_0 = Mock(spec=ScheduledChargingPlan, active=True, current=14, id=0, limit=Limit(selected="amount"))
    plan_mock_1 = Mock(spec=ScheduledChargingPlan, active=True, current=14, id=1, limit=Limit(selected="amount"))
    ct.data.chargemode.scheduled_charging.plans = {"0": plan_mock_0, "1": plan_mock_1}
    # execution
    plan_data = ct._search_plan(14, 60, EvTemplate(), 3, 200, ChargingType.AC.value)

    # evaluation
    if expected_plan_num is None:
        assert plan_data is None
    else:
        assert plan_data.id == expected_plan_num
        assert plan_data.duration == 100


@pytest.mark.parametrize(
    "plan_data, soc, used_amount, selected, expected",
    [
        pytest.param(None, 0, 0, "none", (0, "stop",
                     ChargeTemplate.SCHEDULED_CHARGING_NO_DATE_PENDING, 3), id="no date pending"),
        pytest.param(SelectedPlan(duration=3600), 90, 0, "soc", (0, "stop",
                     ChargeTemplate.SCHEDULED_CHARGING_REACHED_LIMIT_SOC, 1), id="reached limit soc"),
        pytest.param(SelectedPlan(duration=3600), 80, 0, "soc", (6, "pv_charging",
                     ChargeTemplate.SCHEDULED_CHARGING_REACHED_SCHEDULED_SOC, 3), id="reached scheduled soc"),
        pytest.param(SelectedPlan(phases=3, duration=3600), 0, 1000, "amount", (0, "stop",
                     ChargeTemplate.SCHEDULED_CHARGING_REACHED_AMOUNT, 3), id="reached amount"),
        pytest.param(SelectedPlan(remaining_time=299, duration=3600), 0, 999, "amount",
                     (14, "instant_charging", ChargeTemplate.SCHEDULED_CHARGING_IN_TIME.format(
                         14, ChargeTemplate.SCHEDULED_CHARGING_LIMITED_BY_AMOUNT.format(1.0), "07:00"), 1),
                     id="in time, limited by amount"),
        pytest.param(SelectedPlan(remaining_time=299, duration=3600), 79, 0, "soc",
                     (14, "instant_charging", ChargeTemplate.SCHEDULED_CHARGING_IN_TIME.format(
                         14, ChargeTemplate.SCHEDULED_CHARGING_LIMITED_BY_SOC.format(80), "07:00"), 1),
                     id="in time, limited by soc"),
        pytest.param(SelectedPlan(remaining_time=-500, duration=3600, missing_amount=9000, phases=3), 79, 0, "soc",
                     (15.147265077138847, "instant_charging",
                     ChargeTemplate.SCHEDULED_CHARGING_MAX_CURRENT.format(15.15), 3),
                     id="too late, but didn't miss for today"),
        pytest.param(SelectedPlan(remaining_time=-800, duration=780, missing_amount=4600, phases=3), 79, 0, "soc",
                     (16, "instant_charging",
                     ChargeTemplate.SCHEDULED_CHARGING_MAX_CURRENT.format(16), 3),
                     id="few minutes too late, but didn't miss for today"),
        pytest.param(SelectedPlan(remaining_time=301, duration=3600), 79, 0, "soc",
                     (6, "pv_charging", ChargeTemplate.SCHEDULED_CHARGING_USE_PV, 3), id="too early, use pv"),
    ])
def test_scheduled_charging_calc_current(plan_data: SelectedPlan,
                                         soc: int,
                                         used_amount: float,
                                         selected: str,
                                         expected: Tuple[float, str, str, int]):
    # setup
    ct = ChargeTemplate(0)
    plan = ScheduledChargingPlan(active=True, id=0)
    plan.limit.selected = selected
    # json verwandelt Keys in strings
    ct.data.chargemode.scheduled_charging.plans = {"0": plan}

    # execution
    ret = ct.scheduled_charging_calc_current(plan_data, soc, used_amount, 3, 6, 0)

    # evaluation
    assert ret == expected


def test_scheduled_charging_calc_current_no_plans():
    # setup
    ct = ChargeTemplate(0)

    # execution
    ret = ct.scheduled_charging_calc_current(None, 63, 5, 3, 6, 0)

    # evaluation
    assert ret == (0, "stop", ChargeTemplate.SCHEDULED_CHARGING_NO_PLANS_CONFIGURED, 3)


@pytest.mark.parametrize(
    "loading_hour, expected",
    [
        pytest.param(True, (14, "instant_charging", ChargeTemplate.SCHEDULED_CHARGING_CHEAP_HOUR, 3)),
        pytest.param(False, (6, "pv_charging", ChargeTemplate.SCHEDULED_CHARGING_EXPENSIVE_HOUR, 3)),
    ])
def test_scheduled_charging_calc_current_electricity_tariff(loading_hour, expected, monkeypatch):
    # setup
    ct = ChargeTemplate(0)
    plan = ScheduledChargingPlan(active=True)
    plan.limit.selected = "soc"
    ct.data.chargemode.scheduled_charging.plans = {"0": plan}
    ct.data.et.active = True
    mock_et_get_loading_hours = Mock(return_value=[])
    monkeypatch.setattr(data.data.optional_data, "et_get_loading_hours", mock_et_get_loading_hours)
    mock_et_provider_available = Mock(return_value=True)
    monkeypatch.setattr(data.data.optional_data, "et_provider_available", mock_et_provider_available)
    mock_is_list_valid = Mock(return_value=loading_hour)
    monkeypatch.setattr(timecheck, "is_list_valid", mock_is_list_valid)

    # execution
    ret = ct.scheduled_charging_calc_current(SelectedPlan(remaining_time=301, phases=3, duration=3600), 79, 0, 3, 6, 0)

    # evaluation
    assert ret == expected
