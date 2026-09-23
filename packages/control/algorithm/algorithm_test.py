from threading import Event
from unittest.mock import Mock
import pytest

from control import data
from control.algorithm.algorithm import Algorithm
from control.chargemode import Chargemode
from control.chargepoint.chargepoint import Chargepoint
from control.chargepoint.chargepoint_state import ChargepointState
from control.chargepoint.chargepoint_template import CpTemplate, get_chargepoint_template_default
from control.ev.ev import Ev
from control.general import General


@pytest.fixture(autouse=True)
def general() -> None:
    data.data_init(Event())
    data.data.general_data = General()
    data.data.cp_data = {}


def _make_cp(num: int) -> Chargepoint:
    cp = Chargepoint(num, None)
    cp.template = CpTemplate()
    cp.template.data = get_chargepoint_template_default()
    cp.data.set.charging_ev_data = Ev(0)
    cp.data.config.connected_phases = 3
    cp.data.config.auto_phase_switch_hw = True
    cp.data.get.charge_state = False
    cp.data.control_parameter.submode = Chargemode.PV_CHARGING
    cp.data.control_parameter.phases = 3
    cp.data.set.phases_to_use = 3
    cp.data.get.phases_in_use = 3
    cp.data.set.log.imported_since_plugged = 0
    cp.data.set.charge_template.data.chargemode.pv_charging.phases_to_use = 0
    cp.data.set.charging_ev_data.ev_template.data.prevent_phase_switch = False
    cp.data.set.charging_ev_data.ev_template.data.min_current = 6
    data.data.cp_data[f"cp{num}"] = cp
    return cp


class SurplusAtStartParams:
    def __init__(self,
                 name: str,
                 submode: Chargemode,
                 phases_to_use_config: int,
                 usable_surplus: float,
                 min_current: float,
                 expected_phases: int) -> None:
        self.name = name
        self.submode = submode
        self.phases_to_use_config = phases_to_use_config
        self.usable_surplus = usable_surplus
        self.min_current = min_current
        self.expected_phases = expected_phases


surplus_at_start_cases = [
    SurplusAtStartParams("pv charging, enough surplus: start with max phases", submode=Chargemode.PV_CHARGING,
                         phases_to_use_config=0, usable_surplus=5000, min_current=6, expected_phases=3),
    SurplusAtStartParams("pv charging, not enough surplus: start with 1 phase", submode=Chargemode.PV_CHARGING,
                         phases_to_use_config=0, usable_surplus=100, min_current=6, expected_phases=1),
    SurplusAtStartParams("pv charging, fixed phases_to_use: no surplus check, start with 1 phase",
                         submode=Chargemode.PV_CHARGING,
                         phases_to_use_config=3, usable_surplus=3000, min_current=6, expected_phases=1),
    SurplusAtStartParams("instant charging: no surplus check, start with 1 phase", submode=Chargemode.INSTANT_CHARGING,
                         phases_to_use_config=0, usable_surplus=3000, min_current=6, expected_phases=1),
]


@pytest.mark.parametrize("params", surplus_at_start_cases, ids=[c.name for c in surplus_at_start_cases])
def test_check_phases_at_charging_start_uses_surplus(monkeypatch: pytest.MonkeyPatch, params: SurplusAtStartParams):
    # setup
    cp = _make_cp(0)
    cp.data.control_parameter.submode = params.submode
    cp.data.set.charge_template.data.chargemode.pv_charging.phases_to_use = params.phases_to_use_config
    cp.data.set.charging_ev_data.ev_template.data.min_current = params.min_current
    # phases_to_use=1 spiegelt das bestehende Default-Verhalten (get_phases_by_selected_chargemode()
    # startet unconditional einphasig), diese Methode entscheidet, ob das auf max_phase_hw angehoben wird.
    cp.data.control_parameter.phases = 1
    mock_evu = Mock()
    monkeypatch.setattr(mock_evu, "get_usable_surplus", Mock(return_value=params.usable_surplus))
    monkeypatch.setattr(data.data.counter_all_data, "get_evu_counter", Mock(return_value=mock_evu))
    algorithm = Algorithm()
    algorithm.evu_counter = mock_evu

    # execution
    algorithm._check_phases_at_charging_start()

    # evaluation
    assert cp.data.control_parameter.phases == params.expected_phases


def test_check_phases_at_charging_start_does_not_double_count_surplus_across_chargepoints(monkeypatch):
    """ Zwei Ladepunkte starten im selben Zyklus, der Überschuss reicht nur für einen davon
    dreiphasig - der zweite darf nicht denselben, bereits vom ersten beanspruchten Überschuss
    nochmal für sich behaupten. """
    # setup
    cp1 = _make_cp(1)
    cp2 = _make_cp(2)
    # Überschuss reicht für genau einen Ladepunkt (min_current=6 * 3 Phasen * 230V = 4140W),
    # aber nicht für zwei.
    usable_surplus = 5000
    for cp in (cp1, cp2):
        cp.data.control_parameter.phases = 1
        cp.data.set.charging_ev_data.ev_template.data.min_current = 6
    mock_evu = Mock()
    monkeypatch.setattr(mock_evu, "get_usable_surplus", Mock(return_value=usable_surplus))
    monkeypatch.setattr(data.data.counter_all_data, "get_evu_counter", Mock(return_value=mock_evu))
    algorithm = Algorithm()
    algorithm.evu_counter = mock_evu

    # execution
    algorithm._check_phases_at_charging_start()

    # evaluation
    phases = sorted([cp1.data.control_parameter.phases, cp2.data.control_parameter.phases])
    assert phases == [1, 3]


def test_check_phases_at_charging_start_reproduces_matts_log(monkeypatch):
    """ Exakte Werte aus einem realen Log (Matt, 2026-08-08 12:35:43): CUPRA Born (min_current=6,
    max_phases=3) wird an einem 3-phasigen Ladepunkt neu erkannt, Automatik-Umschaltung, noch nicht
    ladend. "Verbleibende Leistung an Zähler 0: 32243.87W" zu diesem Zeitpunkt. Auf master wurde hier
    unconditional phases=1 erzwungen, was trotz der Hardware auf 3 Phasen die unnötige 3->1-Umschaltung
    ausgelöst hat ("LP 4: Umschaltung von 3 auf 1 Phase, dafür wird die Ladung unterbrochen."). """
    # setup
    cp = _make_cp(4)
    cp.data.control_parameter.phases = 1  # Default-Startwert, wie get_phases_by_selected_chargemode() ihn liefert
    cp.data.set.charging_ev_data.ev_template.data.min_current = 6
    cp.data.set.charging_ev_data.ev_template.data.max_phases = 3
    mock_evu = Mock()
    monkeypatch.setattr(mock_evu, "get_usable_surplus", Mock(return_value=32243.87))
    monkeypatch.setattr(data.data.counter_all_data, "get_evu_counter", Mock(return_value=mock_evu))
    algorithm = Algorithm()
    algorithm.evu_counter = mock_evu

    # execution
    algorithm._check_phases_at_charging_start()

    # evaluation
    assert cp.data.control_parameter.phases == 3

    # Downstream-Kette: mit control_parameter.phases jetzt korrekt auf 3 (statt 1, wie auf master),
    # findet _is_phase_switch_required() keinen Mismatch zur Hardware mehr - genau der Aufruf, der in
    # process.py nach dem Algorithmus die eigentliche Umschaltung 3->1 ausgelöst hätte.
    cp.data.control_parameter.state = ChargepointState.NO_CHARGING_ALLOWED
    cp.data.set.phases_to_use = 3  # von _process_charge_stop() beim Abstecken auf phases_in_use gesetzt
    cp.data.get.phases_in_use = 3
    cp.data.set.current = 6
    cp.data.get.charge_state = False
    assert cp._is_phase_switch_required() is False
