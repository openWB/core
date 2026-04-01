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
