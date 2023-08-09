from typing import List, Optional
from unittest.mock import Mock
import pytest
from control import data

from control.chargepoint.chargepoint import Chargepoint
from control.chargepoint.chargepoint_template import CpTemplate
from control.ev import Ev


@pytest.mark.parametrize("phase_1, phases, expected_required_currents",
                         [
                             (0, 1, [6]*3),
                             (1, 1, [6, 0, 0]),
                             (2, 2, [0, 6, 6]),
                             (3, 2, [6, 0, 6]),
                             (3, 3, [6, 6, 6]),
                         ])
def test_get_raw_currents_left_min_current(phase_1: int, phases: int, expected_required_currents: List[float]):
    # setup
    cp = Chargepoint(0, None)
    cp.data.config.phase_1 = phase_1
    cp.data.set.charging_ev_data.data.control_parameter.phases = phases

    # evaluation
    cp.set_required_currents(6)

    # assertion
    assert cp.data.set.charging_ev_data.data.control_parameter.required_currents == expected_required_currents


@pytest.mark.parametrize("required_current, phases, expected_required_current",
                         [
                             pytest.param(12, 1, 12, id="1-phasig, keine Überschreitung"),
                             pytest.param(17, 1, 16, id="1-phasig, Überschreitung des Maximalstroms"),
                             pytest.param(12, 3, 12, id="3-phasig, keine Überschreitung"),
                             pytest.param(21, 3, 20, id="1-phasig, Überschreitung des Maximalstroms"),
                             pytest.param(21, 2, 20, id="2-phasig, Überschreitung des Maximalstroms"),
                         ])
def test_check_min_max_current(required_current, phases, expected_required_current, monkeypatch):
    # setup
    cp = Chargepoint(0, None)
    cp.template = CpTemplate()
    cp.template.data.max_current_multi_phases = 20
    cp.template.data.max_current_single_phase = 16
    mock_ev_check_min_max_current = Mock(return_value=[required_current, None])
    monkeypatch.setattr(Ev, "check_min_max_current", mock_ev_check_min_max_current)
    # evaluation
    ret = cp.check_min_max_current(required_current, phases)

    # assertion
    assert ret == expected_required_current


@pytest.fixture()
def mock_data() -> None:
    data.data_init(Mock())
    data.data.cp_data["cp1"] = Chargepoint(1, None)
    data.data.cp_data["cp1"].data.get.rfid = "1234"


@pytest.mark.parametrize("partner_id, cp1_plug_state, cp0_plug_time, cp1_plug_time, expected_set_rfid",
                         [
                             pytest.param(None, False, None, None, "1234", id="no duo"),
                             pytest.param(1, False, None, None, "1234", id="second cp not plugged"),
                             pytest.param(1, True, "08/08/2023, 11:36:00",
                                          "08/08/2023, 11:37:00", None, id="self first plugged"),
                             pytest.param(1, True, "08/08/2023, 11:37:00",
                                          "08/08/2023, 11:36:00", "1234", id="second first plugged"),
                         ])
def test_link_rfid_to_cp(partner_id: Optional[int],
                         cp1_plug_state: bool,
                         cp0_plug_time: Optional[str],
                         cp1_plug_time: Optional[str],
                         expected_set_rfid: Optional[str],
                         mock_data,
                         monkeypatch):
    # setup
    cp = Chargepoint(0, None)
    cp.chargepoint_module = Mock()
    cp.data.get.rfid = "1234"
    cp.data.set.plug_time = cp0_plug_time
    data.data.cp_data["cp1"].data.get.plug_state = cp1_plug_state
    data.data.cp_data["cp1"].data.set.plug_time = cp1_plug_time
    mock_find_duo_partner = Mock(return_value=partner_id)
    monkeypatch.setattr(Chargepoint, "find_duo_partner", mock_find_duo_partner)

    # execution
    cp._link_rfid_to_cp()

    # evaluation
    assert cp.data.set.rfid == expected_set_rfid
