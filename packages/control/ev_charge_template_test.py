from typing import Dict, NamedTuple, Optional, Tuple
from unittest.mock import Mock

import pytest

from control import data
from control import optional
from control.ev import ChargeTemplate, EvTemplate, EvTemplateData, SelectedPlan
from control.general import General
from helpermodules import timecheck
from helpermodules.abstract_plans import ScheduledChargingPlan, TimeChargingPlan


@pytest.fixture(autouse=True)
def data_module() -> None:
    data.data_init(Mock())
    data.data.general_data = General()
    data.data.optional_data = optional.Optional()


@pytest.mark.parametrize(
    "plans, soc, used_amount_time_charging, plan_found, expected",
    [pytest.param({}, 0, 0, None, (0, "stop", ChargeTemplate.TIME_CHARGING_NO_PLAN_CONFIGURED, None),
                  id="no plan defined"),
     pytest.param({"0": TimeChargingPlan()}, 0, 0,  None,
                  (0, "stop", ChargeTemplate.TIME_CHARGING_NO_PLAN_ACTIVE, None), id="no plan active"),
     pytest.param({"0": TimeChargingPlan()}, 0, 0,  TimeChargingPlan(),
                  (16, "time_charging", None, "Zeitladen-Standard"), id="plan active")
     ])
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
    ret = ct.time_charging(soc, used_amount_time_charging)

    # evaluation
    assert ret == expected


@pytest.mark.parametrize(
    "selected, current_soc, used_amount, expected",
    [
        pytest.param("none", 0, 0, (10, "instant_charging", None), id="without limit"),
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
    ret = ct.instant_charging(current_soc, used_amount)

    # evaluation
    assert ret == expected


@pytest.mark.parametrize(
    "min_soc, min_current, current_soc, expected",
    [
        pytest.param(0, 0, 100, (0, "stop", ChargeTemplate.PV_CHARGING_SOC_REACHED), id="max soc reached"),
        pytest.param(15, 0, 14, (10, "instant_charging", None), id="min soc not reached"),
        pytest.param(15, 8, 15, (8, "instant_charging", None), id="min current configured"),
        pytest.param(15, 0, 15, (6, "pv_charging", None), id="bare pv charging"),
    ])
def test_pv_charging(min_soc: int, min_current: int, current_soc: float,
                     expected: Tuple[int, str, Optional[str]]):
    # setup
    ct = ChargeTemplate(0)
    ct.data.chargemode.pv_charging.min_soc = min_soc
    ct.data.chargemode.pv_charging.min_current = min_current

    # execution
    ret = ct.pv_charging(current_soc, 6)

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
    Params(name="no automatic mode, multi phase", phase_switch_supported=True, chargemode_phases=1,
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
    monkeypatch.setattr(ChargeTemplate, "search_plan", search_plan_mock)
    evt_data = Mock(spec=EvTemplateData, max_current_multi_phases=16, max_current_single_phase=32)
    evt = Mock(spec=EvTemplate, data=evt_data)

    # execution
    ct.scheduled_charging_recent_plan(50, evt, params.phases, 5, params.max_phases, params.phase_switch_supported)

    # evaluation
    assert search_plan_mock.call_args.args[0] == params.expected_max_current
    assert search_plan_mock.call_args.args[3] == params.expected_phases


@pytest.mark.parametrize(
    "selected, phases, expected_duration",
    [
        pytest.param("soc", 1, 2.7950310559006213, id="soc, one phase"),
        pytest.param("amount", 2, 0.12422360248447205, id="amount, two phases"),
    ])
def test_calculate_duration(selected: str, phases: int, expected_duration: float):
    # setup
    ct = ChargeTemplate(0)
    plan = ScheduledChargingPlan()
    plan.limit.selected = selected
    # execution
    duration = ct.calculate_duration(plan, 60, 45, 200, phases)

    # evaluation
    assert duration == expected_duration


@pytest.mark.parametrize(
    "check_duration_return1, check_duration_return2, expected_plan_num",
    [
        pytest.param((-50, False), (60, False), 0, id="too late, but didn't miss date for today"),
        pytest.param((-50, True), (60, False), 1, id="too late and missed date for today"),
        pytest.param((-50, True), (-60, True), 0, id="missed both"),
        pytest.param((50, False), (60, False), 0, id="in time, plan 1"),
        pytest.param((50, False), (40, False), 1, id="in time, plan 2"),
    ])
def test_search_plan(check_duration_return1: Tuple[Optional[float], bool],
                     check_duration_return2: Tuple[Optional[float], bool],
                     expected_plan_num: int,
                     monkeypatch):
    # setup
    calculate_duration_mock = Mock(return_value=100)
    monkeypatch.setattr(ChargeTemplate, "calculate_duration", calculate_duration_mock)
    check_duration_mock = Mock(side_effect=[check_duration_return1, check_duration_return2])
    monkeypatch.setattr(timecheck, "check_duration", check_duration_mock)
    ct = ChargeTemplate(0)
    plan_mock = Mock(spec=ScheduledChargingPlan, active=True, current=14)
    ct.data.chargemode.scheduled_charging.plans = {0: plan_mock, 1: plan_mock}
    # execution
    plan_data = ct.search_plan(14, 60, EvTemplate(), 3, 200)

    # evaluation
    assert plan_data is not None
    assert plan_data.num == expected_plan_num


@pytest.mark.parametrize(
    "plan_data, soc, used_amount, selected, expected",
    [
        pytest.param(None, 0, 0, "none", (0, "stop",
                     ChargeTemplate.SCHEDULED_CHARGING_NO_PLANS_CONFIGURED, 3), id="no plans configured"),
        pytest.param(SelectedPlan(), 90, 0, "soc", (0, "stop",
                     ChargeTemplate.SCHEDULED_CHARGING_REACHED_LIMIT_SOC, 1), id="reached limit soc"),
        pytest.param(SelectedPlan(), 80, 0, "soc", (6, "pv_charging",
                     ChargeTemplate.SCHEDULED_CHARGING_REACHED_SCHEDULED_SOC, 1), id="reached scheduled soc"),
        pytest.param(SelectedPlan(phases=3), 0, 1000, "amount", (0, "stop",
                     ChargeTemplate.SCHEDULED_CHARGING_REACHED_AMOUNT, 3), id="reached amount"),
        pytest.param(SelectedPlan(remaining_time=299), 0, 999, "amount",
                     (14, "instant_charging", ChargeTemplate.SCHEDULED_CHARGING_IN_TIME.format(
                         14, ChargeTemplate.SCHEDULED_CHARGING_LIMITED_BY_AMOUNT.format(1.0), "07:00"), 3),
                     id="in time, limited by amount"),
        pytest.param(SelectedPlan(remaining_time=299), 79, 0, "soc",
                     (14, "instant_charging", ChargeTemplate.SCHEDULED_CHARGING_IN_TIME.format(
                         14, ChargeTemplate.SCHEDULED_CHARGING_LIMITED_BY_SOC.format(80), "07:00"), 3),
                     id="in time, limited by soc"),
        pytest.param(SelectedPlan(remaining_time=0), 79, 0, "soc",
                     (16, "instant_charging", ChargeTemplate.SCHEDULED_CHARGING_MAX_CURRENT.format(16), 3),
                     id="too late, but didn't miss for today"),
        pytest.param(SelectedPlan(remaining_time=301), 79, 0, "soc",
                     (6, "pv_charging", ChargeTemplate.SCHEDULED_CHARGING_USE_PV, 1), id="too early, use pv"),
    ])
def test_scheduled_charging_calc_current(plan_data: SelectedPlan,
                                         soc: int,
                                         used_amount: float,
                                         selected: str,
                                         expected: Tuple[float, str, str, int]):
    # setup
    data.data.optional_data.data.et.active = False
    ct = ChargeTemplate(0)
    plan = ScheduledChargingPlan(active=True)
    plan.limit.selected = selected
    ct.data.chargemode.scheduled_charging.plans = {0: plan}

    # execution
    ret = ct.scheduled_charging_calc_current(plan_data, soc, used_amount, 3, 6)

    # evaluation
    assert ret == expected
