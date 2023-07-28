import pytest

from helpermodules.measurement_logging.conftest import EXPECTED, TOTALS
from helpermodules.measurement_logging.update_daily_yields import update_module_yields


def test_update_module_yields(mock_pub):
    # setup and execution
    [update_module_yields(type, TOTALS) for type in ("bat", "counter", "cp", "pv")]

    # evaluation
    for topic, value in EXPECTED.items():
        for call in mock_pub.mock_calls:
            try:
                if call.args[0] == topic:
                    assert value == call.args[1]
                    break
            except IndexError:
                pass
        else:
            pytest.fail(f"Topic {topic} is missing")
