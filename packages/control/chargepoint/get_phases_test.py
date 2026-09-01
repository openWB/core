from threading import Event
from unittest.mock import Mock
from typing import Optional
import pytest

from control.chargepoint.chargepoint import Chargepoint
from control.chargepoint.chargepoint_state import ChargepointState
from control.chargepoint.chargepoint_template import CpTemplate, get_chargepoint_template_default
from control.ev.ev import Ev
from control.general import General
from control import data
from modules.chargepoints.openwb_pro.chargepoint_module import EvseSignaling


@pytest.fixture
def cp() -> Chargepoint:
    chargep = Chargepoint(0, None)
    chargep.template = CpTemplate()
    chargep.template.data = get_chargepoint_template_default()
    chargep.data.set.charging_ev_data = Ev(0)
    return chargep


@pytest.fixture(autouse=True)
def general() -> None:
    data.data_init(Event())
    data.data.general_data = General()


class Params:
    def __init__(self,
                 name: str,
                 connected_phases: int,
                 auto_phase_switch_hw: bool,
                 prevent_phase_switch: bool,
                 chargemode_phases: int,
                 phases_in_use: int,
                 imported_since_plugged: float,
                 expected_phases: int,
                 timestamp_last_phase_switch: Optional[str] = None,
                 charge_state: bool = False) -> None:
        self.name = name
        self.connected_phases = connected_phases
        self.auto_phase_switch_hw = auto_phase_switch_hw
        self.prevent_phase_switch = prevent_phase_switch
        self.chargemode_phases = chargemode_phases
        self.phases_in_use = phases_in_use
        self.imported_since_plugged = imported_since_plugged
        self.expected_phases = expected_phases
        self.timestamp_last_phase_switch = timestamp_last_phase_switch
        self.charge_state = charge_state


cases = [
    Params("continue using 3", connected_phases=3, auto_phase_switch_hw=False,
           prevent_phase_switch=True, chargemode_phases=3, phases_in_use=3, imported_since_plugged=0,
           expected_phases=3, charge_state=True),
    Params("continue using 1, one phase car", connected_phases=3, auto_phase_switch_hw=False,
           prevent_phase_switch=True, chargemode_phases=3, phases_in_use=1, imported_since_plugged=0,
           expected_phases=1, charge_state=True),
    Params("continue using 1", connected_phases=1, auto_phase_switch_hw=False,
           prevent_phase_switch=True, chargemode_phases=1, phases_in_use=1, imported_since_plugged=0,
           expected_phases=1, charge_state=True),
    Params("don't change during phase switch", connected_phases=3, auto_phase_switch_hw=True,
           prevent_phase_switch=False, chargemode_phases=0, phases_in_use=1, imported_since_plugged=0,
           expected_phases=1, timestamp_last_phase_switch="2022/05/11, 15:00:02"),
    Params("auto phase during charge 3", connected_phases=3, auto_phase_switch_hw=True,
           prevent_phase_switch=False, chargemode_phases=0, phases_in_use=1, imported_since_plugged=0,
           expected_phases=1, charge_state=True),
    Params("auto phase during charge 1", connected_phases=3, auto_phase_switch_hw=True,
           prevent_phase_switch=False, chargemode_phases=0, phases_in_use=3, imported_since_plugged=0,
           expected_phases=3, charge_state=True),
    Params("auto phase before charge no hw switch 3", connected_phases=3, auto_phase_switch_hw=False,
           prevent_phase_switch=False, chargemode_phases=0, phases_in_use=3, imported_since_plugged=0,
           expected_phases=3, charge_state=False),
    Params("auto phase before charge no hw switch 1", connected_phases=3, auto_phase_switch_hw=False,
           prevent_phase_switch=False, chargemode_phases=0, phases_in_use=1, imported_since_plugged=0,
           expected_phases=1, charge_state=False),
    Params("auto phase use min phase at start", connected_phases=3, auto_phase_switch_hw=True,
           prevent_phase_switch=False, chargemode_phases=0, phases_in_use=3, imported_since_plugged=0,
           expected_phases=1, charge_state=False),
]


@pytest.mark.parametrize("params", cases, ids=[c.name for c in cases])
def test_get_phases_by_selected_chargemode(cp: Chargepoint, params: Params):
    # setup
    cp.data.config.connected_phases = params.connected_phases
    cp.data.config.auto_phase_switch_hw = params.auto_phase_switch_hw
    cp.data.get.charge_state = params.charge_state
    cp.data.set.phases_to_use = params.phases_in_use
    cp.data.get.phases_in_use = params.phases_in_use
    cp.data.set.log.imported_since_plugged = params.imported_since_plugged
    charging_ev_data = cp.data.set.charging_ev_data
    charging_ev_data.ev_template.data.prevent_phase_switch = params.prevent_phase_switch
    cp.data.control_parameter.timestamp_last_phase_switch = params.timestamp_last_phase_switch
    cp.data.control_parameter.phases = params.phases_in_use

    # execution
    phases = cp.get_phases_by_selected_chargemode(params.chargemode_phases)

    # evaluation
    assert phases == params.expected_phases


@pytest.mark.parametrize("max_ev_phases, cp_connected_phases, expected_phases",
                         [
                             pytest.param(1, 1, 1),
                             pytest.param(1, 2, 1),
                             pytest.param(1, 3, 1),
                             pytest.param(2, 1, 1),
                             pytest.param(2, 2, 2),
                             pytest.param(2, 3, 2),
                             pytest.param(3, 1, 1),
                             pytest.param(3, 2, 2),
                             pytest.param(3, 3, 3)
                         ])
def test_get_max_phase_hw(max_ev_phases: int, cp_connected_phases: int, expected_phases: int, cp: Chargepoint):
    # setup
    cp.data.config.connected_phases = cp_connected_phases
    cp.data.set.charging_ev_data.ev_template.data.max_phases = max_ev_phases

    # execution
    phases = cp.get_max_phase_hw()
    # evaluation
    assert phases == expected_phases


class SetPhasesParams:
    def __init__(self,
                 name: str,
                 phases: int,
                 prevent_phase_switch: bool,
                 phases_in_use: int,
                 imported_since_plugged: float,
                 phase_switch_supported: bool,
                 expected_phases: int) -> None:
        self.name = name
        self.phases = phases
        self.prevent_phase_switch = prevent_phase_switch
        self.phases_in_use = phases_in_use
        self.imported_since_plugged = imported_since_plugged
        self.phase_switch_supported = phase_switch_supported
        self.expected_phases = expected_phases


cases_set_phases = [
    SetPhasesParams(name="Phases don't change", phases=1, phases_in_use=1, prevent_phase_switch=True,
                    imported_since_plugged=0, phase_switch_supported=True, expected_phases=1),
    SetPhasesParams(name="Charging didn't started yet", phases=1, phases_in_use=3, prevent_phase_switch=True,
                    imported_since_plugged=0, phase_switch_supported=True, expected_phases=1),
    SetPhasesParams(name="EV doesn't support phase wich", phases=1, phases_in_use=3, prevent_phase_switch=True,
                    imported_since_plugged=1, phase_switch_supported=True, expected_phases=3),
    SetPhasesParams(name="Switch phases", phases=1, phases_in_use=3, prevent_phase_switch=False,
                    imported_since_plugged=1, phase_switch_supported=True, expected_phases=1),
    SetPhasesParams(name="Phase switch not supported by cp", phases=1, phases_in_use=3, prevent_phase_switch=False,
                    imported_since_plugged=1, phase_switch_supported=False, expected_phases=3)
]


@pytest.mark.parametrize("params", cases_set_phases, ids=[c.name for c in cases_set_phases])
def test_set_phases(monkeypatch, cp: Chargepoint, params: SetPhasesParams):
    # setup
    mock_phase_switch_supported = Mock(name="phase_switch_supported", return_value=params.phase_switch_supported)
    monkeypatch.setattr(Chargepoint, "hw_supports_phase_switch", mock_phase_switch_supported)
    cp.data.get.phases_in_use = params.phases_in_use
    cp.data.set.log.imported_since_plugged = params.imported_since_plugged
    charging_ev_data = cp.data.set.charging_ev_data
    charging_ev_data.ev_template.data.prevent_phase_switch = params.prevent_phase_switch
    cp.data.control_parameter.phases = params.phases_in_use

    # execution
    phases = cp.set_phases(params.phases, 3)

    # evaluation
    assert phases == params.expected_phases


@pytest.mark.parametrize(
    "auto_phase_switch_hw, evse_signaling, prevent_phase_switch, imported_since_plugged, expected",
    [
        pytest.param(True, EvseSignaling.PWM, False, 10, True, id="supported-without-prevent-flag"),
        pytest.param(False, EvseSignaling.PWM, False, 10, False, id="hardware-disabled"),
        pytest.param(True, EvseSignaling.HLC, False, 10, False, id="hlc-signaling"),
        pytest.param(True, EvseSignaling.PWM, True, 10, False, id="prevent-phase-switch-after-start"),
        pytest.param(True, EvseSignaling.PWM, True, 0, True, id="prevent-phase-switch-before-start"),
    ],
)
def test_hw_supports_phase_switch(cp: Chargepoint,
                                  auto_phase_switch_hw: bool,
                                  evse_signaling: EvseSignaling,
                                  prevent_phase_switch: bool,
                                  imported_since_plugged: float,
                                  expected: bool):
    # setup
    cp.data.config.auto_phase_switch_hw = auto_phase_switch_hw
    cp.data.get.evse_signaling = evse_signaling
    cp.data.set.charging_ev_data.ev_template.data.prevent_phase_switch = prevent_phase_switch
    cp.data.set.log.imported_since_plugged = imported_since_plugged

    # execution
    result = cp.hw_supports_phase_switch()

    # evaluation
    assert result is expected


@pytest.mark.parametrize(
    "retry_failed_phase_switches, failed_phase_switches, expected",
    [
        pytest.param(True, Chargepoint.MAX_FAILED_PHASE_SWITCHES+1, True, id="retry-enabled-limit-reached"),
        pytest.param(True, Chargepoint.MAX_FAILED_PHASE_SWITCHES, False, id="retry-enabled-at-limit"),
        pytest.param(False, Chargepoint.MAX_FAILED_PHASE_SWITCHES-1, True, id="retry-disabled-failed"),
        pytest.param(False, 0, False, id="retry-disabled-not-failed"),
    ],
)
def test_failed_phase_switches_reached(cp: Chargepoint,
                                       retry_failed_phase_switches: bool,
                                       failed_phase_switches: int,
                                       expected: bool):
    # setup
    data.data.general_data.data.chargemode_config.pv_charging.retry_failed_phase_switches = (
        retry_failed_phase_switches
    )
    cp.data.control_parameter.failed_phase_switches = failed_phase_switches

    # execution
    result = cp.failed_phase_switches_reached()

    # evaluation
    assert result is expected


@pytest.mark.parametrize(
    "hw_supports_phase_switch, charge_state, state, failed_phase_switches_reached, expected",
    [
        pytest.param(True, True, ChargepointState.CHARGING_ALLOWED, False, True,
                     id="charging-allowed-and-ready"),
        pytest.param(True, True, ChargepointState.PHASE_SWITCH_DELAY, False, True,
                     id="phase-switch-delay-and-ready"),
        pytest.param(False, True, ChargepointState.CHARGING_ALLOWED, False, False,
                     id="no-hardware-support"),
        pytest.param(True, False, ChargepointState.CHARGING_ALLOWED, False, False,
                     id="not-charging"),
        pytest.param(True, True, ChargepointState.SWITCH_OFF_DELAY, False, False,
                     id="state-not-allowed"),
        pytest.param(True, True, ChargepointState.CHARGING_ALLOWED, True, False,
                     id="failed-switch-limit-reached"),
    ],
)
def test_cp_state_hw_support_phase_switch(monkeypatch,
                                          cp: Chargepoint,
                                          hw_supports_phase_switch: bool,
                                          charge_state: bool,
                                          state: ChargepointState,
                                          failed_phase_switches_reached: bool,
                                          expected: bool):
    # setup
    cp.data.get.charge_state = charge_state
    cp.data.control_parameter.state = state
    monkeypatch.setattr(cp, "hw_supports_phase_switch", Mock(return_value=hw_supports_phase_switch))
    monkeypatch.setattr(cp, "failed_phase_switches_reached", Mock(return_value=failed_phase_switches_reached))

    # execution
    result = cp.cp_state_hw_support_phase_switch()

    # evaluation
    assert result is expected
