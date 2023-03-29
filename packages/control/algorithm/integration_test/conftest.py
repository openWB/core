from dataclasses import dataclass
from unittest.mock import Mock

import pytest

from control import data
from control.bat import Bat
from control.bat_all import BatAll
from control.chargepoint import Chargepoint
from control.counter_all import CounterAll
from control.counter import Counter
from control.ev import Ev
from control.pv import Pv
from control.state_machine import StateMachine
from test_utils.default_hierarchies import NESTED_HIERARCHY


@pytest.fixture(autouse=True)
def data_() -> None:
    data.data_init(Mock())
    data.data.cp_data = {
        "cp3": Chargepoint(3, None),
        "cp4": Chargepoint(4, None),
        "cp5": Chargepoint(5, None)}
    for i in range(3, 6):
        data.data.cp_data[f"cp{i}"].data.config.phase_1 = i-2
        data.data.cp_data[f"cp{i}"].data.set.charging_ev = i
        data.data.cp_data[f"cp{i}"].data.set.charging_ev_data = Ev(i)
        data.data.cp_data[f"cp{i}"].data.get.plug_state = True
        data.data.cp_data[f"cp{i}"].data.set.plug_time = f"12/01/2022, 15:0{i}:11"
        data.data.cp_data[f"cp{i}"].data.set.charging_ev_data.ev_template.data.nominal_difference = 2
    data.data.cp_data["cp3"].data.set.charging_ev_data.ev_template.data.min_current = 10
    data.data.bat_data.update({"bat2": Bat(2), "all": BatAll()})
    data.data.pv_data.update({"pv1": Pv(1)})
    data.data.counter_data.update({
        "counter0": Counter(0),
        "counter6": Counter(6)})
    data.data.counter_data["counter0"].data.get.currents = [0, 2, 1]*3
    data.data.counter_data["counter0"].data.get.power = 690
    data.data.counter_data["counter0"].data.config.max_currents = [32]*3
    data.data.counter_data["counter0"].data.config.max_total_power = 22000
    data.data.counter_data["counter6"].data.get.currents = [0, 4, 2]
    data.data.counter_data["counter6"].data.get.power = 1380
    data.data.counter_data["counter6"].data.config.max_currents = [16]*3
    data.data.counter_data["counter6"].data.config.max_total_power = 11000
    data.data.counter_all_data = CounterAll()
    data.data.counter_all_data.data.get.hierarchy = NESTED_HIERARCHY


@dataclass
class ParamsExpectedSetCurrent:
    expected_current_cp3: float = 0
    expected_current_cp4: float = 0
    expected_current_cp5: float = 0


def assert_expected_current(params: ParamsExpectedSetCurrent):
    for i in range(3, 6):
        assert data.data.cp_data[f"cp{i}"].data.set.current == getattr(params, f"expected_current_cp{i}")


@pytest.fixture()
def all_cp_not_charging():
    for i in range(3, 6):
        charging_ev_data = data.data.cp_data[f"cp{i}"].data.set.charging_ev_data
        data.data.cp_data[f"cp{i}"].data.get.currents = [0]*3
        data.data.cp_data[f"cp{i}"].data.get.charge_state = False
        charging_ev_data.data.control_parameter.state = StateMachine.NO_CHARGING_ALLOWED
