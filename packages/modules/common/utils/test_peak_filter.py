from dataclasses import dataclass
import pytest
from unittest.mock import MagicMock
from modules.common.utils.peak_filter import PeakFilter
from modules.common.fault_state import FaultState
from modules.common.component_type import ComponentType


class DummyFaultState(FaultState):
    def __init__(self):
        self.warnings = []

    def warning(self, msg):
        self.warnings.append(msg)


class DummyConfig:
    def __init__(self, max_power):
        self.max_power = max_power
        self.max_total_power = max_power
        self.max_ac_out = max_power


class DummyData:
    def __init__(self, max_power):
        self.data = MagicMock()
        self.data.config = DummyConfig(max_power)


@pytest.fixture(autouse=True)
def patch_data(monkeypatch):
    import modules.common.utils.peak_filter as pf
    pf.data = MagicMock()
    pf.data.data = MagicMock()
    pf.data.data.counter_data = {"counter1": DummyData(3000)}
    pf.data.data.pv_data = {"pv1": DummyData(2000)}
    pf.data.data.bat_data = {"bat1": DummyData(1000)}
    pf.data.data.general_data = MagicMock()
    pf.data.data.general_data.data = MagicMock()
    pf.data.data.general_data.data.control_interval = 10
    yield


@dataclass
class Params:
    name: str
    component_type: ComponentType
    previous_imported: float
    previous_exported: float
    power: float
    imported: float
    exported: float
    expected_imported: float
    expected_exported: float
    expect_exception: bool = False


cases = [
    Params("Power Peak Zähler positiv", ComponentType.COUNTER, 1000, 500, 11000, 1300, 800, None, None, True),
    Params("Power Peak Zähler negativ", ComponentType.COUNTER, 1000, 500, -11000, 1300, 800, None, None, True),
    Params("Power Peak Wechselrichter", ComponentType.INVERTER, 1000, 500, 11000, 1005, 505, 1005, 505, True),
    Params("Power Peak Speicher positiv", ComponentType.BAT, 1000, 500, 11000, 1005, 505, 1005, 505, True),
    Params("Power Peak Speicher negativ", ComponentType.BAT, 1000, 500, -11000, 1005, 505, 1005, 505, True),
    Params("Imp/ Exp Zähler - Werte valide", ComponentType.COUNTER, 1000, 500, 900, 1005, 505, 1005, 505),
    Params("Imp/ Exp Wechselrichter - Werte valide", ComponentType.INVERTER, 1000, 500, 1500, 1005, 505, 1005, 505),
    Params("Imp/ Exp Speicher - Werte valide", ComponentType.BAT, 1000, 500, 400, 1005, 505, 1005, 505),
    Params("Imp/ Exp Zähler - Werte invalide", ComponentType.COUNTER, 1000, 500, 1000, 1300, 800, None, None),
    Params("Imp/ Exp Zähler - Import invalide", ComponentType.COUNTER, 1000, 500, 1000, 1300, 505, None, 505),
    Params("Imp/ Exp Zähler - Export invalide", ComponentType.COUNTER, 1000, 500, 1000, 1005, 800, 1005, None),
    Params("Imp/ Exp Wechselrichter - Werte invalide", ComponentType.INVERTER, 1000, 500, 1500, 1300, 800, None, None),
    Params("Imp/ Exp Wechselrichter - Import invalide", ComponentType.INVERTER, 1000, 500, 1500, 1300, 505, None, 505),
    Params("Imp/ Exp Wechselrichter - Export invalide", ComponentType.INVERTER, 1000, 500, 1500, 1005, 800, 1005, None),
    Params("Imp/ Exp Speicher - Werte invalide", ComponentType.BAT, 1000, 500, 400, 1300, 800, None, None),
    Params("Imp/ Exp Speicher - Import invalide", ComponentType.BAT, 1000, 500, 400, 1300, 505, None, 505),
    Params("Imp/ Exp Speicher - Export invalide", ComponentType.BAT, 1000, 500, 400, 1005, 800, 1005, None),
    Params("Imp/ Exp Speicher - Import > 50Y", ComponentType.BAT, 500000000, 500, 400, 500000000, 505, None, 505),
    Params("Imp/ Exp Speicher - Export > 50Y", ComponentType.BAT, 1000, 500000000, 400, 1005, 500000000, 1005, None),
    Params("Imp/ Exp Speicher - Export ~ 45Y", ComponentType.BAT,
           1000, 400000000, 400, 1005, 400000000, 1005, 400000000),
    Params("Imp/ Exp Speicher - Import ~ 45Y", ComponentType.BAT,
           400000000, 500, 400, 400000000, 505, 400000000, 505)
]


@pytest.mark.parametrize("params", cases, ids=[c.name for c in cases])
def test_check_values_valid(params):
    fs = DummyFaultState()
    pf = PeakFilter(params.component_type, 1, fs)
    pf.imported = params.previous_imported
    pf.exported = params.previous_exported
    if params.expect_exception:
        with pytest.raises(Exception):
            imp, exp = pf.check_values(params.power, params.imported, params.exported)
    else:
        imp, exp = pf.check_values(params.power, params.imported, params.exported)
        assert imp == params.expected_imported
        assert exp == params.expected_exported


def test_check_total_energy_forward_jump_within_bound_is_capped_and_catches_up_over_cycles():
    fs = DummyFaultState()
    pf = PeakFilter(ComponentType.COUNTER, 1, fs)

    allowed_deviation = 10
    max_energy = 1_000_000_000

    # Vorwaertssprung genau am Rand von MAX_SMOOTHABLE_JUMP_FACTOR * allowed_deviation (zB Zaehler/WR,
    # der seinen Stand nur sprunghaft aktualisiert): wird auf die erlaubte Differenz begrenzt statt
    # verworfen, und als neue Basis gemerkt.
    checked, previous = pf.check_total_energy(1100, 1000, allowed_deviation, max_energy)
    assert checked == 1010
    assert previous == 1010

    # Rohwert bleibt stehen - naechster Zyklus holt schrittweise weiter auf.
    checked, previous = pf.check_total_energy(1100, previous, allowed_deviation, max_energy)
    assert checked == 1020
    assert previous == 1020

    for _ in range(8):
        checked, previous = pf.check_total_energy(1100, previous, allowed_deviation, max_energy)
    assert checked == 1100
    assert previous == 1100

    # Danach wird mit kleinen, plausiblen Differenzen normal weitergezaehlt.
    checked, previous = pf.check_total_energy(1105, previous, allowed_deviation, max_energy)
    assert checked == 1105
    assert previous == 1105

    # Rueckwaertssprung: letzter gueltiger Hoechststand bleibt erhalten.
    checked, previous = pf.check_total_energy(1000, previous, allowed_deviation, max_energy)
    assert checked == 1105
    assert previous == 1105

    # Unterhalb des Hoechststands wird weiterhin gewartet.
    checked, previous = pf.check_total_energy(1090, previous, allowed_deviation, max_energy)
    assert checked == 1105
    assert previous == 1105

    # Naechster gleicher oder hoeherer Wert wird wieder zugelassen.
    checked, previous = pf.check_total_energy(1105, previous, allowed_deviation, max_energy)
    assert checked == 1105
    assert previous == 1105

    checked, previous = pf.check_total_energy(1110, previous, allowed_deviation, max_energy)
    assert checked == 1110
    assert previous == 1110


def test_check_total_energy_forward_jump_beyond_bound_falls_back_to_reject_then_accept():
    fs = DummyFaultState()
    pf = PeakFilter(ComponentType.COUNTER, 1, fs)

    allowed_deviation = 10
    max_energy = 1_000_000_000

    # Sprung deutlich groesser als MAX_SMOOTHABLE_JUMP_FACTOR * allowed_deviation (zB nach einer
    # laengeren Verbindungsunterbrechung mit echtem Nachholbedarf, nicht nur einem groben Zaehlertakt):
    # wird NICHT geglaettet, sondern wie vor dieser Aenderung einmal verworfen und bei Bestaetigung im
    # naechsten Zyklus sofort in voller Hoehe uebernommen.
    checked, previous = pf.check_total_energy(2000, 1000, allowed_deviation, max_energy)
    assert checked is None
    assert previous == 2000

    checked, previous = pf.check_total_energy(2000, previous, allowed_deviation, max_energy)
    assert checked == 2000
    assert previous == 2000


def test_check_total_energy_recovery_after_too_high_previous_value():
    fs = DummyFaultState()
    pf = PeakFilter(ComponentType.COUNTER, 1, fs)

    allowed_deviation = 10
    max_energy = 3000

    # Vorheriger Wert lag ueber dem 50-Jahres-Limit - niedrigerer Folgewert wird einmal verworfen
    # und als neue Vergleichsbasis gesetzt (unabhaengig vom Cap-Verhalten bei Vorwaertssprueingen).
    checked, previous = pf.check_total_energy(4000, 2900, allowed_deviation, max_energy)
    assert checked is None
    assert previous == 4000

    checked, previous = pf.check_total_energy(2800, previous, allowed_deviation, max_energy)
    assert checked is None
    assert previous == 2800

    # Danach wird ein plausibler Folgewert wieder zugelassen.
    checked, previous = pf.check_total_energy(2805, previous, allowed_deviation, max_energy)
    assert checked == 2805
    assert previous == 2805
