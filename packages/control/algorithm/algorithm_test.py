from unittest.mock import Mock
import pytest

from control import data
from control.algorithm.algorithm import Algorithm
from control.chargemode import Chargemode
from control.chargepoint.chargepoint import Chargepoint
from control.chargepoint.chargepoint_state import ChargepointState
from control.counter import Counter
from control.general import General


@pytest.fixture(autouse=True)
def data_fixture() -> None:
    data.data_init(Mock())
    data.data.general_data = General()
    data.data.cp_data = {"cp2": Chargepoint(2, None)}
    data.data.counter_data = {"counter0": Counter(0)}
    data.data.counter_all_data.data.get.hierarchy = [
        {"id": 0,
         "type": "counter",
         "children": [
             {"id": 1,
              "type": "inverter",
              "children": []},
             {"id": 2,
              "type": "cp",
              "children": []}]}]


@pytest.mark.parametrize("control_range, evu_power, evu_currents, evu_voltages, cp_power, cp_currents",
                         [pytest.param([-230, 0], -84.08, [-2.42, 4.69, -2.66], [239, 237.8, 237.6], 1823.86, [7.81, -0.06, 0.06], id="Einspeisung, im Regelbereich"),
                          pytest.param([-230, 0], 41.96, [-2.4, 5.22, -2.64], [238.7, 237.7, 237.7], 1939.72, [8.31, -0.06, 0.06], id="Einspeisung, über Regelbereich"),
                          pytest.param([-230, 0], -690, [-1, -1, -1], [230, 230, 230], 1610, [7, 0, 0], id="Einspeisung bei 230V Spannung, unter Regelbereich"),
                          pytest.param([-230, 0], -115, [0, -0.5, 0], [230, 230, 230], 2185, [9.5, 0, 0], id="Einspeisung bei 230V Spannung, im Regelbereich"),
                          pytest.param([-230, 0], -115, [0, -0.49, 0], [235, 235, 235], 2185, [9.3, 0, 0], id="Einspeisung bei 235V Spannung, im Regelbereich"),
                          pytest.param([-230, 0], 235, [0, 1, 0], [235, 235, 235], 2535, [10.87, 0, 0], id="Einspeisung bei 235V Spannung, über Regelbereich"),
                          pytest.param([0, 230], -230, [0, -1, 0], [230, 230, 230], 2070, [9, 0, 0], id="Bezug bei 230V Spannung, unter Regelbereich"),
                          pytest.param([0, 230], 115, [0, 0.5, 0], [230, 230, 230], 2415, [10.5, 0, 0], id="Bezug bei 230V Spannung, im Regelbereich"),
                          pytest.param([0, 230], 115, [0, 0.49, 0], [235, 235, 235], 2415, [10.3, 0, 0], id="Bezug bei 235V Spannung, im Regelbereich"),
                          pytest.param([0, 230], 705, [1, 1, 1], [235, 235, 235], 3005, [12.8, 0, 0], id="Bezug bei 235V Spannung, über Regelbereich"),
                          pytest.param([-115, 115], -230, [0, -1, 0], [230, 230, 230], 2070, [9, 0, 0], id="Ausgeglichen bei 230V Spannung, unter Regelbereich"),
                          pytest.param([-115, 115], 0, [0, 0, 0], [230, 230, 230], 2300, [10, 0, 0], id="Ausgeglichen bei 230V Spannung, im Regelbereich"),
                          pytest.param([-115, 115], 0, [0, 0, 0], [235, 235, 235], 2300, [9.8, 0, 0], id="Ausgeglichen bei 235V Spannung, im Regelbereich"),
                          pytest.param([-115, 115], 235, [0, 1, 0], [235, 235, 235], 2535, [10.8, 0, 0], id="Ausgeglichen bei 235V Spannung, über Regelbereich")
                          ]
                         )
def test_calc_current(control_range, evu_power, evu_currents, evu_voltages, cp_power, cp_currents, monkeypatch):
    # setup
    data.data.general_data.data.chargemode_config.pv_charging.control_range = control_range
    cp = data.data.cp_data["cp2"]
    cp.data.config.phase_1 = 2
    cp.data.control_parameter.state = ChargepointState.CHARGING_ALLOWED
    cp.data.control_parameter.chargemode = Chargemode.PV_CHARGING
    cp.data.control_parameter.submode = Chargemode.PV_CHARGING
    cp.data.control_parameter.phases = 1
    cp.data.control_parameter.required_current = 6
    cp.data.control_parameter.required_currents = [0, 6, 0]
    cp.data.set.charging_ev = 0
    cp.data.get.currents = cp_currents
    cp.data.get.power = cp_power
    counter = data.data.counter_data["counter0"]
    counter.data.config.max_currents = [35, 35, 35]
    counter.data.config.max_total_power = 24000
    counter.data.get.currents = evu_currents
    counter.data.get.voltages = evu_voltages
    counter.data.get.power = evu_power
    counter._set_power_left()
    counter._set_current_left()
    a = Algorithm()

    # execution
    a.calc_current()

    # evaluation
    average_voltage = sum(cp.data.get.voltages)/len(cp.data.get.voltages)
    initial_power_left = cp.data.get.power - counter.data.get.power
    new_power = cp.data.set.current * average_voltage
    # calculated surplus is in control range
    assert control_range[0] < int(new_power - initial_power_left) < control_range[1]
