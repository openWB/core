from unittest.mock import Mock
import pytest

from control.algorithm import additional_current
from control.chargepoint import Chargepoint, ChargepointData, Set
from control.ev import ChargeTemplate, Ev
from control.loadmanagement import LimitingValue


@pytest.mark.parametrize(
    "set_current, limit, expected_msg",
    [pytest.param(7, None, None, id="unverändert"),
     pytest.param(
        6, LimitingValue.CURRENT,
        f"Es kann nicht mit der vorgegebenen Stromstärke geladen werden{LimitingValue.CURRENT.value.format('Garage')}",
         id="begrenzt durch Strom"),
     pytest.param(
        6, LimitingValue.POWER,
        f"Es kann nicht mit der vorgegebenen Stromstärke geladen werden{LimitingValue.POWER.value.format('Garage')}",
         id="begrenzt durch Leistung"),
     pytest.param(
        6, LimitingValue.UNBALANCED_LOAD,
        f"Es kann nicht mit der vorgegebenen Stromstärke geladen werden"
        f"{LimitingValue.UNBALANCED_LOAD.value.format('Garage')}",
        id="begrenzt durch Schieflast"),
     ])
def test_set_loadmangement_message(set_current, limit, expected_msg, monkeypatch):
    # setup
    ev = Ev(0)
    ev.charge_template = ChargeTemplate(0)
    ev.data.control_parameter.required_currents = [7]*3
    cp1 = Chargepoint(1, None)
    cp1.data = ChargepointData(set=Set(current=set_current))
    mockget_component_name_by_id = Mock(return_value="Garage")
    monkeypatch.setattr(additional_current, "get_component_name_by_id", mockget_component_name_by_id)

    # execution
    additional_current.AdditionalCurrent()._set_loadmangement_message(7, limit, cp1, Mock())

    # evaluation
    assert cp1.data.get.state_str == expected_msg
