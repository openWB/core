from unittest.mock import Mock

from helpermodules.measurement_logging import write_log
from helpermodules.measurement_logging.conftest import NAMES, TOTALS
from helpermodules.measurement_logging.write_log import get_names


def test_get_names(monkeypatch):
    # setup
    component_names_mock = Mock(side_effect=["Speicher", "Zähler", "Wechselrichter"])
    monkeypatch.setattr(write_log, "get_component_name_by_id", component_names_mock)
    # execution
    names = get_names(TOTALS, {"sh1": "Smarthome1"})

    # evaluation
    assert names == NAMES
