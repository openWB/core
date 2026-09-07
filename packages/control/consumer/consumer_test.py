from unittest.mock import Mock
from typing import Dict, List, Optional, Tuple
import datetime

import pytest

from helpermodules.abstract_plans import (ScheduledChargingPlan, ScheduledPlanConsumer, TimeChargingPlan,
                                          TimeChargingPlanConsumer)
from helpermodules import timecheck
from control import optional
from control import data
from control.general import General
from control.bat_all import BatAll
from control.chargemode import Chargemode
from control.consumer.consumer import Consumer
from control.consumer.consumer_data import WaitForStartStates
from control.consumer.usage import ConsumerUsage


@pytest.fixture(autouse=True)
def mock_data() -> None:
    data.data_init(Mock())
    data.data.general_data = General()
    data.data.optional_data = optional.Optional()


@pytest.fixture
def consumer() -> Consumer:
    load = Consumer(1)
    load.data.usage.type = ConsumerUsage.CONTINUOUS
    load.data.config.min_current = 6
    load.data.config.max_power = 2300
    load.data.config.connected_phases = 1
    load.data.get.voltages = [230]
    load.data.get.currents = [10]
    return load


def test_get_parameter_clears_previous_state_string_when_switch_interval_is_active(consumer: Consumer):
    # setup
    consumer.data.set.switch_interval_elapsed = False
    consumer.data.set.state_str_prev = "previous state"

    # execution
    _, _, state_string, _, _ = consumer.get_parameter()

    # evaluation
    assert state_string is None


@pytest.mark.parametrize(
    ("wait_for_start_active",
     "state", "currents",
     "func_result",
     "expected_result",
     "expected_state",
     "func_calls"),
    [
        pytest.param(
            False,
            WaitForStartStates.WAIT_FOR_DEVICE_START,
            [0]*3,
            (11, "ok", Chargemode.PV_CHARGING),
            (11, "ok", Chargemode.PV_CHARGING),
            WaitForStartStates.WAIT_FOR_DEVICE_START,
            1,
            id="wait-for-start-disabled-passthrough",
        ),
        pytest.param(
            True,
            WaitForStartStates.WAIT_FOR_DEVICE_START,
            [10]*3,
            (9, "running", Chargemode.PV_CHARGING),
            (0, Consumer.WAIT_FOR_STOPPED_DEVICE, Chargemode.STOP),
            WaitForStartStates.WAIT_FOR_STOPPED_DEVICE,
            0,
            id="wait-for-device-start-charge-detected",
        ),
        pytest.param(
            True,
            WaitForStartStates.WAIT_FOR_DEVICE_START,
            [0]*3,
            (9, "running", Chargemode.PV_CHARGING),
            (10, Consumer.WAIT_FOR_DEVICE_START, Chargemode.INSTANT_CHARGING),
            WaitForStartStates.WAIT_FOR_DEVICE_START,
            0,
            id="wait-for-device-start-no-charge",
        ),
        pytest.param(
            True,
            WaitForStartStates.WAIT_FOR_STOPPED_DEVICE,
            [0]*3,
            (8, "pv ok", Chargemode.PV_CHARGING),
            (8, f"{Consumer.DEVICE_WAITING_FOR_START} pv ok", Chargemode.PV_CHARGING),
            WaitForStartStates.DEVICE_WAITING_FOR_START,
            1,
            id="wait-for-stopped-device-started-waiting",
        ),
        pytest.param(
            True,
            WaitForStartStates.DEVICE_WAITING_FOR_START,
            [10]*3,
            (7, "started", Chargemode.INSTANT_CHARGING),
            (7, "started", Chargemode.INSTANT_CHARGING),
            WaitForStartStates.START_SIGNAL_RECEIVED,
            1,
            id="device-waiting-start-signal-received",
        ),
        pytest.param(
            True,
            WaitForStartStates.START_SIGNAL_RECEIVED,
            [10]*3,
            (10, "continue", Chargemode.PV_CHARGING),
            (10, "continue", Chargemode.PV_CHARGING),
            WaitForStartStates.START_SIGNAL_RECEIVED,
            1,
            id="start-signal-received-passthrough",
        ),
    ],
)
def test_wait_for_start_handler(
        consumer: Consumer,
        wait_for_start_active: bool,
        state: WaitForStartStates,
        currents: List[float],
        func_result: Tuple[int, str, Optional[Chargemode]],
        expected_result: Tuple[int, str, Optional[Chargemode]],
        expected_state: WaitForStartStates,
        func_calls: int,
):
    # setup
    consumer.data.usage.wait_for_start_active = wait_for_start_active
    consumer.data.set.wait_for_start_state = state
    consumer.data.get.currents = currents
    charging_func = Mock(return_value=func_result)

    # execution
    result = consumer.wait_for_start_handler(charging_func)

    # evaluation
    assert result == expected_result
    assert consumer.data.set.wait_for_start_state == expected_state
    assert charging_func.call_count == func_calls


@pytest.mark.parametrize(
    "plans, plan_found, expected",
    [
        pytest.param({}, None, (0,
                     Consumer.TIME_CHARGING_NO_PLAN_CONFIGURED, Chargemode.STOP), id="no plan defined"),
        pytest.param({"0": TimeChargingPlanConsumer(id=0)}, None,
                     (0, Consumer.TIME_CHARGING_NO_PLAN_ACTIVE, Chargemode.STOP), id="no plan active"),
        pytest.param({"0": TimeChargingPlanConsumer(id=0)}, TimeChargingPlanConsumer(id=0),
                     (10, None, Chargemode.TIME_CHARGING), id="plan active"),
        pytest.param({"0": TimeChargingPlanConsumer(id=0)}, None,
                     (0, Consumer.TIME_CHARGING_NO_PLAN_ACTIVE, Chargemode.STOP),
                     id="plan defined but not found"),
    ]
)
def test_time_charging(plans: Dict[int, TimeChargingPlanConsumer],
                       plan_found: TimeChargingPlanConsumer,
                       expected: Tuple[float, Optional[str], Chargemode],
                       consumer: Consumer,
                       monkeypatch: pytest.MonkeyPatch):
    # setup
    consumer.data.usage.time_charging.plans = plans
    check_plans_timeframe_mock = Mock(return_value=plan_found)
    monkeypatch.setattr(timecheck, "check_plans_timeframe", check_plans_timeframe_mock)

    # execution
    ret = consumer.time_charging()

    # evaluation
    assert ret == expected


@pytest.mark.parametrize(
    "min_bat_soc, charging_allowed_mock, soc, expected",
    [
        pytest.param(80, False, 81, (0, Consumer.TIME_CHARGING_CONFLICT_ACTIVE_BAT_CONTROL, Chargemode.STOP),
                     id="Konflikt mit aktiver Speichersteuerung -> nicht laden"),
        pytest.param(80, True, 79, (0, Consumer.TIME_CHARGING_MIN_BAT_SOC_REACHED, Chargemode.STOP),
                     id="Mindest-SoC des Speichers unterschritten -> nicht laden"),
        pytest.param(80, True, 80, (10, None, Chargemode.TIME_CHARGING), id="laden erlaubt"),
        pytest.param(None, True, 80, (10, None, Chargemode.TIME_CHARGING),
                     id="Mindest-SoC-Beachtung nicht konfiguriert, laden erlaubt"),
    ]
)
def test_time_charging_min_bat_soc(min_bat_soc: Optional[int],
                                   charging_allowed_mock: bool,
                                   soc: float,
                                   expected: Tuple[float, Optional[str], Chargemode],
                                   consumer: Consumer,
                                   monkeypatch: pytest.MonkeyPatch):
    # setup
    plan = TimeChargingPlan(id=0)
    plan.min_bat_soc = min_bat_soc
    consumer.data.usage.time_charging.plans = [plan]
    check_plans_timeframe_mock = Mock(return_value=plan)
    monkeypatch.setattr(timecheck, "check_plans_timeframe", check_plans_timeframe_mock)

    data.data.bat_all_data = BatAll()
    data.data.bat_all_data.data.config.configured = True
    data.data.bat_all_data.data.get.soc = soc
    monkeypatch.setattr(data.data.bat_all_data, "time_charging_min_bat_soc_allowed",
                        Mock(return_value=charging_allowed_mock))

    # execution
    ret = consumer.time_charging()

    # evaluation
    assert ret == expected


def test_instant_charging(consumer: Consumer):
    # setup & execution
    ret = consumer.instant_charging()

    # evaluation
    assert ret == (10, None, Chargemode.INSTANT_CHARGING)


def test_pv_charging(consumer: Consumer):
    # setup & execution
    ret = consumer.pv_charging()

    # evaluation
    # bei Dauerverbrauchern wird Maximal-Strom angenommen
    assert ret == (10, None, Chargemode.PV_CHARGING)


@pytest.mark.parametrize(
    "on_time, plan_duration, diff_end_date, expected",
    [
        pytest.param(0, 3600, 6000, (2400, 3600), id="no-runtime-yet"),
        pytest.param(1200, 3600, 6000, (3600, 2400), id="already-running"),
        pytest.param(3700, 3600, 1000, (1100, -100), id="duration-exceeded"),
    ],
)
def test_calc_remaining_time(on_time: float,
                             plan_duration: float,
                             diff_end_date: float,
                             expected: Tuple[float, float],
                             consumer: Consumer):
    # setup
    consumer.data.set.on_time = on_time
    plan = Mock(duration=plan_duration)

    # execution
    ret = consumer._calc_remaining_time(plan, diff_end_date)

    # evaluation
    assert ret == expected


@pytest.mark.parametrize(
    "end_time_mock, expected_plan_num",
    [
        pytest.param([1000, 1500, 2000], 0, id="nächster Zieltermin Plan 0"),
        pytest.param([-100, 45000, 50000], 0, id="Plan 0 abgelaufen, nächster Tag"),
        pytest.param([1500, 2000, 1000], 2, id="nächster Zieltermin Plan 2"),
        pytest.param([-1201]*3, 0, id="kein Plan"),
    ])
def test_scheduled_charging_recent_plan(end_time_mock,
                                        expected_plan_num: Optional[int],
                                        consumer: Consumer,
                                        monkeypatch: pytest.MonkeyPatch):
    # setup
    calculate_duration_mock = Mock(return_value=(100, 500))
    monkeypatch.setattr(Consumer, "_calc_remaining_time", calculate_duration_mock)
    check_end_time_mock = Mock(side_effect=end_time_mock)
    monkeypatch.setattr(timecheck, "check_end_time", check_end_time_mock)
    plan_mock_0 = Mock(spec=ScheduledPlanConsumer, active=True, id=0)
    plan_mock_1 = Mock(spec=ScheduledPlanConsumer, active=True, id=1)
    plan_mock_2 = Mock(spec=ScheduledPlanConsumer, active=True, id=2)
    plans = [plan_mock_0, plan_mock_1, plan_mock_2]

    # execution
    selected_plan, remaining_time, duration = consumer._find_recent_plan(plans)

    # evaluation
    if selected_plan:
        assert selected_plan.id == expected_plan_num
        assert remaining_time == 100
        assert duration == 500
    else:
        assert selected_plan is None
        assert remaining_time == 0
        assert duration == 0


@pytest.mark.parametrize(
    "plan, remaining_time, duration, expected",
    [
        pytest.param(None, 0, 0, (0, Consumer.SCHEDULED_CHARGING_NO_DATE_PENDING, Chargemode.STOP),
                     id="no date pending"),
        pytest.param(ScheduledPlanConsumer(), 0, 0, (0, Consumer.SCHEDULED_REACHED_MAX_ON_TIME,
                     Chargemode.STOP), id="reached max on time"),
        pytest.param(ScheduledPlanConsumer(), 299, 3600, (10, None, Chargemode.INSTANT_CHARGING),
                     id="in time"),
        pytest.param(ScheduledPlanConsumer(), -500, 3600, (10, None, Chargemode.INSTANT_CHARGING),
                     id="too late, but didn't miss for today"),
        pytest.param(ScheduledPlanConsumer(), -800, 780, (10, None, Chargemode.INSTANT_CHARGING),
                     id="few minutes too late, but didn't miss for today"),
        pytest.param(ScheduledPlanConsumer(), 601, 3600, (10, Consumer.SCHEDULED_CHARGING_USE_PV.format(
            "um 8:50 Uhr"), Chargemode.PV_CHARGING), id="too early, use pv"),
    ])
def test_scheduled_charging_calc_current(plan: Optional[ScheduledPlanConsumer],
                                         remaining_time: float,
                                         duration: float,
                                         expected: Tuple[float, Optional[str], Chargemode],
                                         consumer: Consumer,):
    # setup
    if plan is not None:
        plan.id = 0
    # json verwandelt Keys in strings
    consumer.data.usage.scheduled_charging.plans = [plan]

    # execution
    ret = consumer.scheduled_charging_calc_current(plan, remaining_time, duration)

    # evaluation
    assert ret == expected


def test_scheduled_charging_calc_current_no_plans(consumer: Consumer):
    # execution
    ret = consumer.scheduled_charging_calc_current(None, 0, 0)

    # evaluation
    assert ret == (0, Consumer.SCHEDULED_CHARGING_NO_PLANS_CONFIGURED, Chargemode.STOP)


LOADING_HOURS_TODAY = [datetime.datetime(
    year=2022, month=5, day=16, hour=8, minute=0).timestamp()]

LOADING_HOURS_TOMORROW = [datetime.datetime(
    year=2022, month=5, day=17, hour=8, minute=0).timestamp()]


@pytest.mark.parametrize(
    "is_loading_hour, loading_hours, expected",
    [
        pytest.param(True, LOADING_HOURS_TODAY + LOADING_HOURS_TOMORROW,
                     (
                         10,
                         Consumer.SCHEDULED_CHARGING_CHEAP_HOUR.format(
                             "Eingeschaltet wird jetzt sowie morgen 8:00."),
                         Chargemode.INSTANT_CHARGING),
                     id="cheap_hour_charge_with_instant_charging"),
        pytest.param(False, LOADING_HOURS_TODAY,
                     (
                         10,
                         Consumer.SCHEDULED_CHARGING_EXPENSIVE_HOUR.format(
                             "Eingeschaltet wird heute 8:00."),
                         Chargemode.PV_CHARGING),
                     id="expensive_hour_charge_with_pv"),
        pytest.param(False, LOADING_HOURS_TODAY,
                     (
                         10,
                         Consumer.SCHEDULED_CHARGING_EXPENSIVE_HOUR.format(
                             "Eingeschaltet wird heute 8:00."),
                         Chargemode.PV_CHARGING),
                     id="expensive_hour_no_charge_with_pv "),
        pytest.param(False, LOADING_HOURS_TODAY + LOADING_HOURS_TOMORROW,
                     (
                         10,
                         Consumer.SCHEDULED_CHARGING_EXPENSIVE_HOUR.format(
                             "Eingeschaltet wird heute 8:00 sowie morgen 8:00."),
                         Chargemode.PV_CHARGING),
                     id="expensive_hour_no_charge_with_pv scheduled for tomorrow"),
    ])
def test_scheduled_charging_calc_current_electricity_tariff(
        is_loading_hour: bool,
        loading_hours: List[float],
        expected: Tuple[float, Optional[str], Chargemode],
        monkeypatch: pytest.MonkeyPatch,
        consumer: Consumer):
    # setup
    datetime_mock = Mock(wraps=datetime.datetime)
    datetime_mock.now.return_value = datetime.datetime.fromtimestamp(LOADING_HOURS_TODAY[0])
    monkeypatch.setattr(datetime, "datetime", datetime_mock)

    plan = ScheduledChargingPlan()
    consumer.data.usage.scheduled_charging.plans = [plan]
    # für Github-Test keinen Zeitstempel verwenden
    mock_ep_get_loading_hours = Mock(return_value=loading_hours)
    monkeypatch.setattr(data.data.optional_data, "ep_get_loading_hours", mock_ep_get_loading_hours)
    mock_is_list_valid = Mock(return_value=is_loading_hour)
    monkeypatch.setattr(data.data.optional_data, "ep_is_charging_allowed_hours_list", mock_is_list_valid)
    data.data.optional_data.data.electricity_pricing.configured = True

    # execution
    ret = consumer.scheduled_charging_calc_current(plan, remaining_time=601, duration=3600)

    # evaluation
    assert ret == expected
