from typing import List
from unittest.mock import Mock
import pytest

from control.chargepoint import Chargepoint, CpTemplate
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
