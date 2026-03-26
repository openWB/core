from unittest.mock import Mock
import pytest
from modules.common.utils.peak_filter import PeakFilter


@pytest.fixture(autouse=True)
def mock_peak_filter(monkeypatch) -> Mock:
    mock = Mock(return_value=(100000, 200000))
    # mock = Mock(side_effect=lambda imported, exported: (imported, exported))
    monkeypatch.setattr(PeakFilter, 'check_values', mock)
    return mock
