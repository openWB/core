import threading
from unittest.mock import Mock
from typing import Optional
import pytest


from control import chargepoint
from control.chargepoint import Chargepoint, CpTemplate
from control.ev import Ev
from control.general import General
from helpermodules import pub
from control import data


@pytest.fixture
def cp() -> Chargepoint:
    chargep = Chargepoint(0, None)
    chargep.template = CpTemplate()
    chargep.template.data = chargepoint.get_chargepoint_template_default()
    chargep.data.set.charging_ev_data = Ev(0)
    return chargep


@pytest.fixture(autouse=True)
def general() -> None:
    data.data_init(threading.Event())
    data.data.general_data = General()


@pytest.fixture(autouse=True)
def mock_pub(monkeypatch) -> None:
    pub_mock = Mock()
    pub_mock.pub.return_value = None
    monkeypatch.setattr(pub, 'PubSingleton', pub_mock)


class Params:
    def __init__(self,
                 name: str,
                 connected_phases: int,
                 auto_phase_switch_hw: bool,
                 max_phases: int,
                 prevent_phase_switch: bool,
                 chargemode_phases: int,
                 phases_in_use: int,
                 imported_since_plugged: float,
                 expected_phases: int,
                 timestamp_perform_phase_switch: Optional[str] = None,
                 charge_state: bool = False) -> None:
        self.name = name
        self.connected_phases = connected_phases
        self.auto_phase_switch_hw = auto_phase_switch_hw
        self.max_phases = max_phases
        self.prevent_phase_switch = prevent_phase_switch
        self.chargemode_phases = chargemode_phases
        self.phases_in_use = phases_in_use
        self.imported_since_plugged = imported_since_plugged
        self.expected_phases = expected_phases
        self.timestamp_perform_phase_switch = timestamp_perform_phase_switch
        self.charge_state = charge_state


cases = [
    Params("continue using 3", connected_phases=3, auto_phase_switch_hw=False, max_phases=3,
           prevent_phase_switch=True, chargemode_phases=3, phases_in_use=3, imported_since_plugged=0,
           expected_phases=3),
    Params("continue using 1", connected_phases=1, auto_phase_switch_hw=False, max_phases=1,
           prevent_phase_switch=True, chargemode_phases=1, phases_in_use=1, imported_since_plugged=0,
           expected_phases=1),
    Params("prevent switch after charge start", connected_phases=3, auto_phase_switch_hw=True, max_phases=3,
           prevent_phase_switch=True, chargemode_phases=3, phases_in_use=1, imported_since_plugged=10,
           expected_phases=1),
    Params("switch before charge start", connected_phases=3, auto_phase_switch_hw=True, max_phases=3,
           prevent_phase_switch=True, chargemode_phases=3, phases_in_use=1, imported_since_plugged=0,
           expected_phases=3),
    Params("don't change during phase switch", connected_phases=3, auto_phase_switch_hw=True, max_phases=3,
           prevent_phase_switch=False, chargemode_phases=0, phases_in_use=1, imported_since_plugged=0,
           expected_phases=1, timestamp_perform_phase_switch="2022/05/11, 15:00:02"),
    Params("auto phase during charge 3", connected_phases=3, auto_phase_switch_hw=True, max_phases=3,
           prevent_phase_switch=False, chargemode_phases=0, phases_in_use=1, imported_since_plugged=0,
           expected_phases=1, charge_state=True),
    Params("auto phase during charge 1", connected_phases=3, auto_phase_switch_hw=True, max_phases=3,
           prevent_phase_switch=False, chargemode_phases=0, phases_in_use=3, imported_since_plugged=0,
           expected_phases=3, charge_state=True),
    Params("auto phase before charge no hw switch 3", connected_phases=3, auto_phase_switch_hw=False, max_phases=3,
           prevent_phase_switch=False, chargemode_phases=0, phases_in_use=3, imported_since_plugged=0,
           expected_phases=3, charge_state=False),
    Params("auto phase before charge no hw switch 1", connected_phases=3, auto_phase_switch_hw=False, max_phases=3,
           prevent_phase_switch=False, chargemode_phases=0, phases_in_use=1, imported_since_plugged=0,
           expected_phases=3, charge_state=False),
    Params("auto phase use min phase at start", connected_phases=3, auto_phase_switch_hw=True, max_phases=3,
           prevent_phase_switch=False, chargemode_phases=0, phases_in_use=3, imported_since_plugged=0,
           expected_phases=1, charge_state=False),
    Params("cp phases < chargemode phases", connected_phases=1, auto_phase_switch_hw=False, max_phases=3,
           prevent_phase_switch=False, chargemode_phases=3, phases_in_use=1, imported_since_plugged=0,
           expected_phases=1),
    Params("cp phases < ev phases", connected_phases=1, auto_phase_switch_hw=False, max_phases=3,
           prevent_phase_switch=False, chargemode_phases=3, phases_in_use=1, imported_since_plugged=0,
           expected_phases=1),
    Params("cp phases > ev phases", connected_phases=3, auto_phase_switch_hw=False, max_phases=1,
           prevent_phase_switch=False, chargemode_phases=3, phases_in_use=3, imported_since_plugged=0,
           expected_phases=1),
    Params("cp phases > ev phases, in use 0", connected_phases=3, auto_phase_switch_hw=False, max_phases=1,
           prevent_phase_switch=False, chargemode_phases=3, phases_in_use=0, imported_since_plugged=0,
           expected_phases=1)
]


@pytest.mark.parametrize("params", cases, ids=[c.name for c in cases])
def test_get_phases(monkeypatch, cp: Chargepoint, params: Params):
    # setup
    mock_chargemode_phases = Mock(name="chargemode_phases", return_value=params.chargemode_phases)
    monkeypatch.setattr(data.data.general_data, "get_phases_chargemode", mock_chargemode_phases)

    cp.data.config.connected_phases = params.connected_phases
    cp.data.config.auto_phase_switch_hw = params.auto_phase_switch_hw
    cp.data.get.charge_state = params.charge_state
    cp.data.get.phases_in_use = params.phases_in_use
    cp.data.set.phases_to_use = params.phases_in_use
    cp.data.set.log.imported_since_plugged = params.imported_since_plugged
    charging_ev_data = cp.data.set.charging_ev_data
    charging_ev_data.ev_template.data.max_phases = params.max_phases
    charging_ev_data.ev_template.data.prevent_phase_switch = params.prevent_phase_switch
    charging_ev_data.data.control_parameter.timestamp_perform_phase_switch = params.timestamp_perform_phase_switch
    charging_ev_data.data.control_parameter.phases = params.phases_in_use

    # execution
    phases = cp.get_phases()

    # evaluation
    assert phases == params.expected_phases
