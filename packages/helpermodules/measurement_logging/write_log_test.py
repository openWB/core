from unittest.mock import Mock

from helpermodules.measurement_logging import write_log
from helpermodules.measurement_logging.write_log import get_names


def test_get_names(daily_log_totals, monkeypatch):
    # setup
    component_names_mock = Mock(side_effect=["Speicher", "Zähler", "Wechselrichter"])
    monkeypatch.setattr(write_log, "get_component_name_by_id", component_names_mock)
    # execution
    names = get_names(daily_log_totals, {"sh1": "Smarthome1"})

    # evaluation
    assert names == {'bat2': "Speicher",
                     'counter0': "Zähler",
                     'cp3': "cp3",
                     'cp4': "Standard-Ladepunkt",
                     'cp5': "Standard-Ladepunkt",
                     'cp6': "Standard-Ladepunkt",
                     'pv1': "Wechselrichter",
                     "sh1": "Smarthome1"}
