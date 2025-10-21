import datetime
from typing import Dict, Optional, Tuple
from unittest.mock import Mock

import pytest

from control import data
from control import optional
from control.chargepoint.control_parameter import ControlParameter
from control.ev.charge_template import SelectedPlan
from control.chargepoint.charging_type import ChargingType
from control.ev.charge_template import ChargeTemplate
from control.ev.ev_template import EvTemplate, EvTemplateData
from control.general import General
from control.text import BidiState
from helpermodules import timecheck
from helpermodules.abstract_plans import Limit, ScheduledChargingPlan, TimeChargingPlan, ScheduledLimit


@pytest.fixture(autouse=True)
def data_module() -> None:
    data.data_init(Mock())
    data.data.general_data = General()
    data.data.optional_data = optional.Optional()


@pytest.mark.parametrize(
    "plans, soc, used_amount_time_charging, plan_found, expected",
    [
        pytest.param({}, 0, 0, None, (0, "stop", ChargeTemplate.TIME_CHARGING_NO_PLAN_CONFIGURED, None, None),
                     id="no plan defined"),
        pytest.param({"0": TimeChargingPlan(id=0)}, 0, 0,  None,
                     (0, "stop", ChargeTemplate.TIME_CHARGING_NO_PLAN_ACTIVE, None, None), id="no plan active"),
        pytest.param({"0": TimeChargingPlan(id=0)}, 0, 0,  TimeChargingPlan(id=0),
                     (16, "time_charging", None, 0, 1), id="plan active"),
        pytest.param({"0": TimeChargingPlan(id=0, limit=Limit(selected="soc"))}, 100, 0,
                     TimeChargingPlan(id=0, limit=Limit(selected="soc")),
                     (0, "stop", ChargeTemplate.TIME_CHARGING_SOC_REACHED, 0, 1),
                     id="plan active, soc is reached"),
        pytest.param({"0": TimeChargingPlan(id=0, limit=Limit(selected="soc"))}, 40, 0,
                     TimeChargingPlan(id=0, limit=Limit(selected="soc")),
                     (16, "time_charging", None, 0, 1), id="plan active, soc is not reached"),
        pytest.param({"0": TimeChargingPlan(id=0, limit=Limit(selected="soc"))}, None, 0,
                     TimeChargingPlan(id=0, limit=Limit(selected="soc")),
                     (16, "time_charging", None, 0, 1), id="plan active, soc is not defined"),
        pytest.param({"0": TimeChargingPlan(id=0, limit=Limit(selected="amount", amount=1000))}, 0, 1500,
                     TimeChargingPlan(id=0, limit=Limit(selected="amount", amount=1000)),
                     (0, "stop", ChargeTemplate.TIME_CHARGING_AMOUNT_REACHED, 0, 1),
                     id="plan active, used_amount_time_charging is reached"),
        pytest.param({"0": TimeChargingPlan(id=0, limit=Limit(selected="amount", amount=1000))}, 0, 500,
                     TimeChargingPlan(id=0, limit=Limit(selected="amount", amount=1000)),
                     (16, "time_charging", None, 0, 1),
                     id="plan active, used_amount_time_charging is not reached"),
        pytest.param({"0": TimeChargingPlan(id=0)}, 0, 0,  None,
                     (0, "stop", ChargeTemplate.TIME_CHARGING_NO_PLAN_ACTIVE, None, None),
                     id="plan defined but not found"),
    ]
)
def test_time_charging(plans: Dict[int, TimeChargingPlan], soc: float, used_amount_time_charging: float,
                       plan_found: TimeChargingPlan,
                       expected: Tuple[int, str, Optional[str], Optional[str]],
                       monkeypatch):
    # setup
    ct = ChargeTemplate()
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
        pytest.param("none", 0, 0, (16, "instant_charging", None, 3), id="without limit"),
        pytest.param("soc", None, 0, (16, "instant_charging", None, 3), id="limit soc: soc not defined"),
        pytest.param("soc", 49, 0, (16, "instant_charging", None, 3), id="limit soc: soc not reached"),
        pytest.param("soc", 50, 0, (0, "stop", ChargeTemplate.SOC_REACHED, 3),
                     id="limit soc: soc reached"),
        pytest.param("amount", 0, 999, (16, "instant_charging", None, 3), id="limit amount: amount not reached"),
        pytest.param("amount", 0, 1000, (0, "stop", ChargeTemplate.AMOUNT_REACHED, 3),
                     id="limit amount: amount reached"),
    ])
def test_instant_charging(selected: str, current_soc: float, used_amount: float,
                          expected: Tuple[int, str, Optional[str]]):
    # setup
    data.data.optional_data.data.et.active = False
    ct = ChargeTemplate()
    ct.data.chargemode.instant_charging.limit.selected = selected
    ct.data.chargemode.instant_charging.limit.amount = 1000

    # execution
    ret = ct.instant_charging(current_soc, used_amount, ChargingType.AC.value)

    # evaluation
    assert ret == expected


@pytest.mark.parametrize(
    "min_soc, min_current, limit_selected, current_soc, used_amount, expected",
    [
        pytest.param(0, 0, "amount", 14, 1500, (0, "stop", ChargeTemplate.AMOUNT_REACHED, 0), id="max amount reached"),
        pytest.param(0, 0, "soc", 100, 900, (0, "stop", ChargeTemplate.SOC_REACHED, 0), id="max soc reached"),
        pytest.param(15, 0, None, 14, 900, (10, "instant_charging", ChargeTemplate.PV_CHARGING_SOC_CHARGING, 3),
                     id="min soc not reached"),
        pytest.param(15, 0, None, None, 900, (6, "pv_charging", None, 0), id="soc not defined"),
        pytest.param(15, 8, None, 15, 900, (8, "instant_charging", ChargeTemplate.PV_CHARGING_MIN_CURRENT_CHARGING, 0),
                     id="min current configured"),
        pytest.param(15, 0, None, 15, 900, (6, "pv_charging", None, 0), id="bare pv charging"),
    ])
def test_pv_charging(min_soc: int,
                     min_current: int,
                     limit_selected: str,
                     current_soc: float,
                     used_amount: float,
                     expected: Tuple[int, str, Optional[str], int]):
    # setup
    ct = ChargeTemplate()
    ct.data.chargemode.pv_charging.min_soc = min_soc
    ct.data.chargemode.pv_charging.min_current = min_current
    ct.data.chargemode.pv_charging.phases_to_use = 0
    ct.data.chargemode.pv_charging.phases_to_use_min_soc = 3
    ct.data.chargemode.pv_charging.limit.selected = limit_selected
    ct.data.chargemode.pv_charging.limit.amount = 1000
    ct.data.chargemode.pv_charging.limit.soc = 90
    data.data.bat_all_data.data.config.configured = True

    # execution
    ret = ct.pv_charging(current_soc, 6, ChargingType.AC.value, used_amount)

    # evaluation
    assert ret == expected


@pytest.mark.parametrize("phases_to_use, calc_duration, max_hw_phases, phase_switch_supported, expected",
                         [
                             pytest.param(0, [(1000, 3)], 1, True, (5000, 3, 1, 1000), id="automatic, one hw phase"),
                             pytest.param(0, [(1000, 3)], 3, False, (5000, 3, 2, 1000),
                                          id="automatic, no phase switch"),
                             pytest.param(0, [(1000, 3), (7000, 3)], 3, True, (5000, 3, 3, 1000), id="automatic, 3p"),
                             pytest.param(0, [(500, 3), (1500, 3)], 3, True, (4500, 3, 1, 1500), id="automatic, 1p"),
                             pytest.param(3, [(5000, 3)], 3, True, (1000, 3, 3, 5000), id="3p"),
                             pytest.param(1, [(5000, 3)], 3, True, (1000, 3, 1, 5000), id="1p"),
                         ])
def test_calc_remaining_time(phases_to_use,
                             calc_duration,
                             max_hw_phases,
                             phase_switch_supported,
                             expected, monkeypatch):
    # setup
    ct = ChargeTemplate()
    plan = ScheduledChargingPlan(phases_to_use=phases_to_use)
    calculate_duration_mock = Mock(side_effect=calc_duration)
    monkeypatch.setattr(ChargeTemplate, "_calculate_duration", calculate_duration_mock)
    evt = Mock(spec=EvTemplate, data=Mock(spec=EvTemplateData, battery_capacity=85))

    # execution
    remaining_time, missing_amount, phases, duration = ct._calc_remaining_time(
        plan, 6000, 50, evt, 3000, max_hw_phases, phase_switch_supported, ChargingType.AC.value, 2, 0, False)
    # end time 16.5.22 10:00

    # evaluation
    assert (remaining_time, missing_amount, phases, duration) == expected


@pytest.mark.parametrize(
    "selected, phases, bidi_charging_enabled, expected_duration, expected_missing_amount",
    [
        pytest.param("soc", 1, False, 10062.111801242236, 9000, id="soc, one phase"),
        pytest.param("amount", 2, False, 447.2049689440994, 800, id="amount, two phases"),
        pytest.param("soc", 2, True, 3240.0, 9000, id="bidi"),
    ])
def test_calculate_duration(selected: str,
                            phases: int,
                            bidi_charging_enabled: bool,
                            expected_duration: float,
                            expected_missing_amount: float):
    # setup
    ct = ChargeTemplate()
    plan = ScheduledChargingPlan(bidi_charging_enabled=bidi_charging_enabled)
    plan.limit.selected = selected
    # execution
    duration, missing_amount = ct._calculate_duration(
        plan, 60, 45000, 200, phases, ChargingType.AC.value, EvTemplate(), bidi_charging_enabled)

    # evaluation
    assert duration == expected_duration
    assert missing_amount == expected_missing_amount


@pytest.mark.parametrize(
    "end_time_mock, expected_plan_num",
    [
        pytest.param([1000, 1500, 2000], 0, id="nächster Zieltermin Plan 0"),
        pytest.param([-100, 1000, 2000], 1, id="Plan 0 abgelaufen, Plan 1 innerhalb der nächsten 12h"),
        pytest.param([-100, 45000, 50000], 0, id="Plan 0 abgelaufen, Plan 1 nicht innerhalb der nächsten 12h"),
        pytest.param([1500, 2000, 1000], 2, id="nächster Zieltermin Plan 2"),
        pytest.param([None]*3, 0, id="kein Plan"),
    ])
def test_scheduled_charging_recent_plan(end_time_mock,
                                        expected_plan_num: Optional[int],
                                        monkeypatch):
    # setup
    calculate_duration_mock = Mock(return_value=(100, 3000, 3, 500))
    monkeypatch.setattr(ChargeTemplate, "_calc_remaining_time", calculate_duration_mock)
    check_end_time_mock = Mock(side_effect=end_time_mock)
    monkeypatch.setattr(timecheck, "check_end_time", check_end_time_mock)
    control_parameter = ControlParameter()
    ct = ChargeTemplate()
    plan_mock_0 = Mock(spec=ScheduledChargingPlan, active=True, current=14, id=0, limit=Limit(selected="amount"))
    plan_mock_1 = Mock(spec=ScheduledChargingPlan, active=True, current=14, id=1, limit=Limit(selected="amount"))
    plan_mock_2 = Mock(spec=ScheduledChargingPlan, active=True, current=14, id=2, limit=Limit(selected="amount"))
    plans = [plan_mock_0, plan_mock_1, plan_mock_2]

    # execution
    selected_plan = ct._find_recent_plan(
        plans, 60, EvTemplate(), 200, 3, True, ChargingType.AC.value, 1652688000, control_parameter, 0, False)

    # evaluation
    if selected_plan:
        assert selected_plan.plan.id == expected_plan_num
    else:
        assert selected_plan is None


@pytest.mark.parametrize(
    "plan_data, soc, used_amount, selected, bidi_charging_enabled, expected",
    [
        pytest.param(None, 0, 0, "none", False, (0, "stop",
                     ChargeTemplate.SCHEDULED_CHARGING_NO_DATE_PENDING, 3), id="no date pending"),
        pytest.param(SelectedPlan(duration=3600), 90, 0, "soc", False, (0, "stop",
                     ChargeTemplate.SCHEDULED_CHARGING_REACHED_MAX_AND_LIMIT_SOC, 1), id="reached limit soc"),
        pytest.param(SelectedPlan(duration=3600), 80, 0, "soc", False, (6, "pv_charging",
                     ChargeTemplate.SCHEDULED_CHARGING_REACHED_SCHEDULED_SOC, 0), id="reached scheduled soc"),
        pytest.param(SelectedPlan(duration=3600), 80, 0, "soc", True, (6, "bidi_charging",
                     ChargeTemplate.SCHEDULED_CHARGING_BIDI, 3), id="reached scheduled soc, bidi"),
        pytest.param(SelectedPlan(phases=3, duration=3600), 0, 1000, "amount", False, (0, "stop",
                     ChargeTemplate.SCHEDULED_CHARGING_REACHED_AMOUNT, 3), id="reached amount"),
        pytest.param(SelectedPlan(remaining_time=299, duration=3600), 0, 999, "amount",
                     False, (14, "instant_charging", ChargeTemplate.SCHEDULED_CHARGING_IN_TIME.format(
                         14, ChargeTemplate.SCHEDULED_CHARGING_LIMITED_BY_AMOUNT.format(1.0), "07:00"), 1),
                     id="in time, limited by amount"),
        pytest.param(SelectedPlan(remaining_time=299, duration=3600), 79, 0, "soc",
                     False, (14, "instant_charging", ChargeTemplate.SCHEDULED_CHARGING_IN_TIME.format(
                         14, ChargeTemplate.SCHEDULED_CHARGING_LIMITED_BY_SOC.format(80), "07:00"), 1),
                     id="in time, limited by soc"),
        pytest.param(SelectedPlan(remaining_time=-500, duration=3600, missing_amount=9000, phases=3), 79, 0, "soc",
                     False, (15.147265077138847, "instant_charging",
                     ChargeTemplate.SCHEDULED_CHARGING_MAX_CURRENT.format(15.15), 3),
                     id="too late, but didn't miss for today"),
        pytest.param(SelectedPlan(remaining_time=-800, duration=780, missing_amount=4600, phases=3), 79, 0, "soc",
                     False, (16, "instant_charging",
                     ChargeTemplate.SCHEDULED_CHARGING_MAX_CURRENT.format(16), 3),
                     id="few minutes too late, but didn't miss for today"),
        pytest.param(SelectedPlan(remaining_time=301, duration=3600), 79, 0, "soc",
                     False, (6, "pv_charging", ChargeTemplate.SCHEDULED_CHARGING_USE_PV.format("um 8:45 Uhr"), 0),
                     id="too early, use pv"),
    ])
def test_scheduled_charging_calc_current(plan_data: SelectedPlan,
                                         soc: int,
                                         used_amount: float,
                                         selected: str,
                                         bidi_charging_enabled: bool,
                                         expected: Tuple[float, str, str, int]):
    # setup
    ct = ChargeTemplate()
    plan = ScheduledChargingPlan(active=True, id=0)
    plan.limit.selected = selected
    plan.bidi_charging_enabled = bidi_charging_enabled
    # json verwandelt Keys in strings
    ct.data.chargemode.scheduled_charging.plans = [plan]
    if plan_data:
        plan_data.plan = plan

    # execution
    ret = ct.scheduled_charging_calc_current(plan_data, soc, used_amount, 3, 6,
                                             0, ChargingType.AC.value, EvTemplate(), BidiState.BIDI_CAPABLE)

    # evaluation
    assert ret == expected


def test_scheduled_charging_calc_current_no_plans():
    # setup
    ct = ChargeTemplate()

    # execution
    ret = ct.scheduled_charging_calc_current(
        None, 63, 5, 3, 6, 0, ChargingType.AC.value, EvTemplate(), BidiState.BIDI_CAPABLE)

    # evaluation
    assert ret == (0, "stop", ChargeTemplate.SCHEDULED_CHARGING_NO_PLANS_CONFIGURED, 3)


LOADING_HOURS_TODAY = [datetime.datetime(
    year=2022, month=5, day=16, hour=8, minute=0).timestamp()]

LOADING_HOURS_TOMORROW = [datetime.datetime(
    year=2022, month=5, day=17, hour=8, minute=0).timestamp()]


@pytest.mark.parametrize(
    "is_loading_hour, current_soc, soc_scheduled, sco_limit, loading_hours, expected",
    [
        pytest.param(True, 79, 80, 90, LOADING_HOURS_TODAY + LOADING_HOURS_TOMORROW,
                     (
                         14,
                         "instant_charging",
                         ChargeTemplate.SCHEDULED_CHARGING_CHEAP_HOUR.format(
                             "Geladen wird jetzt und zu folgenden Uhrzeiten: morgen 8:00."),
                         3),
                     id="cheap_hour_charge_with_instant_charging"),
        pytest.param(True, 79, 80, 70, LOADING_HOURS_TODAY,
                     (
                         14,
                         "instant_charging",
                         ChargeTemplate.SCHEDULED_CHARGING_CHEAP_HOUR.format(
                             "Geladen wird jetzt und zu folgenden Uhrzeiten: ."),
                         3),
                     id="SOC limit reached but scheduled SOC not, no further loading hours"),
        pytest.param(False, 79, 80, 90, LOADING_HOURS_TODAY,
                     (
                         6,
                         "pv_charging",
                         ChargeTemplate.SCHEDULED_CHARGING_EXPENSIVE_HOUR.format(
                             "Geladen wird zu folgenden Uhrzeiten: 8:00."),
                         0),
                     id="expensive_hour_charge_with_pv"),
        pytest.param(False, 79, 80, 70, LOADING_HOURS_TODAY,
                     (
                         0,
                         "stop",
                         ChargeTemplate.SCHEDULED_CHARGING_EXPENSIVE_HOUR_REACHED_MAX_SOC.format(
                             "Geladen wird zu folgenden Uhrzeiten: 8:00."),
                         3),
                     id="expensive_hour_no_charge_with_pv "),
        pytest.param(False, 79, 80, 70, LOADING_HOURS_TODAY + LOADING_HOURS_TOMORROW,
                     (
                         0,
                         "stop",
                         ChargeTemplate.SCHEDULED_CHARGING_EXPENSIVE_HOUR_REACHED_MAX_SOC.format(
                             "Geladen wird zu folgenden Uhrzeiten: 8:00, morgen 8:00."),
                         3),
                     id="expensive_hour_no_charge_with_pv scheduled for tomorrow"),
        pytest.param(False, 79, 60, 80, LOADING_HOURS_TODAY,
                     (
                         6,
                         "pv_charging",
                         ChargeTemplate.SCHEDULED_CHARGING_REACHED_SCHEDULED_SOC.format(
                             ""),
                         0),
                     id="expensive_hour_pv_charging"),
        pytest.param(False, 79, 60, 50, LOADING_HOURS_TODAY,
                     (
                         0,
                         "stop",
                         ChargeTemplate.SCHEDULED_CHARGING_REACHED_MAX_AND_LIMIT_SOC.format(
                             ""),
                         3),
                     id="scheduled and limit SOC reached"),
    ])
def test_scheduled_charging_calc_current_electricity_tariff(
        is_loading_hour, current_soc, soc_scheduled, sco_limit, loading_hours, expected, monkeypatch):
    # setup
    datetime_mock = Mock(wraps=datetime.datetime)
    datetime_mock.now.return_value = datetime.datetime.fromtimestamp(LOADING_HOURS_TODAY[0])
    monkeypatch.setattr(datetime, "datetime", datetime_mock)

    ct = ChargeTemplate()
    plan = ScheduledChargingPlan(active=True,
                                 limit=ScheduledLimit(selected="soc", soc_scheduled=soc_scheduled, soc_limit=sco_limit))
    plan.et_active = True
    plan.limit.selected = "soc"
    ct.data.chargemode.scheduled_charging.plans = [plan]
    # für Github-Test keinen Zeitstempel verwenden
    mock_et_get_loading_hours = Mock(return_value=loading_hours)
    monkeypatch.setattr(data.data.optional_data, "et_get_loading_hours", mock_et_get_loading_hours)
    mock_is_list_valid = Mock(return_value=is_loading_hour)
    monkeypatch.setattr(data.data.optional_data, "et_charging_is_allowed", mock_is_list_valid)

    # execution
    ret = ct.scheduled_charging_calc_current(
        SelectedPlan(plan=plan, remaining_time=301, phases=3, duration=3600),
        current_soc, 0, 3, 6, 0, ChargingType.AC.value, EvTemplate(), BidiState.BIDI_CAPABLE)

    # evaluation
    assert ret == expected
