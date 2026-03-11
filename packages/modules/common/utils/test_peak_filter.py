import pytest
from unittest.mock import MagicMock
from modules.common.utils.peak_filter import PeakFilter
from modules.common.fault_state import FaultState


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


def test_check_power_valid():
    fs = DummyFaultState()
    pf = PeakFilter("counter", 1, fs)
    pf.check_power(1000, 1500)  # Should not raise


def test_check_power_invalid():
    fs = DummyFaultState()
    pf = PeakFilter("counter", 1, fs)
    with pytest.raises(Exception):
        pf.check_power(1000, 2500)


def test_check_imported_exported_valid():
    fs = DummyFaultState()
    pf = PeakFilter("counter", 1, fs)
    pf.imported = 1000
    pf.exported = 500
    imp, exp = pf.check_imported_exported(2000, 1010, 510)
    assert imp == 1010
    assert exp == 510


def test_check_imported_exported_invalid():
    fs = DummyFaultState()
    pf = PeakFilter("counter", 1, fs)
    pf.imported = 1000
    pf.exported = 500
    imp, exp = pf.check_imported_exported(1000, 1300, 800)
    assert imp is None
    assert exp is None
    assert fs.warnings


def test_check_values_counter():
    fs = DummyFaultState()
    pf = PeakFilter("counter", 1, fs)
    pf.imported = 1000
    pf.exported = 500
    imp, exp = pf.check_values(900, 1005, 505)
    assert imp == 1005
    assert exp == 505


def test_check_values_inverter():
    fs = DummyFaultState()
    pf = PeakFilter("inverter", 1, fs)
    pf.imported = 1000
    pf.exported = 500
    imp, exp = pf.check_values(1500, 1005, 505)
    assert imp == 1005
    assert exp == 505


def test_check_values_bat():
    fs = DummyFaultState()
    pf = PeakFilter("bat", 1, fs)
    pf.imported = 1000
    pf.exported = 500
    imp, exp = pf.check_values(400, 1005, 505)
    assert imp == 1005
    assert exp == 505
