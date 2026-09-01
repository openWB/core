from unittest.mock import Mock
import pytest
from modules.common.utils.peak_filter import PeakFilter


@pytest.fixture(autouse=True)
def mock_peak_filter(monkeypatch) -> Mock:
    mock = Mock(side_effect=lambda power, imported=None, exported=None: (imported, exported))
    monkeypatch.setattr(PeakFilter, 'check_values', mock)
    return mock
