import pytest

from control.algorithm import additional_current
from control.chargepoint.chargepoint import Chargepoint, ChargepointData
from control.chargepoint.chargepoint_data import Set
from control.chargepoint.control_parameter import ControlParameter
from control.ev.charge_template import ChargeTemplate
from control.ev.ev import Ev
from control.limiting_value import LoadmanagementLimit
from control.loadmanagement import LimitingValue


@pytest.mark.parametrize(
    "set_current, limit, expected_msg",
    [pytest.param(7, LoadmanagementLimit(None,  None), None, id="unverändert"),
     pytest.param(
        6, LoadmanagementLimit(LimitingValue.CURRENT.value.format('Garage'), LimitingValue.CURRENT),
        f"Es kann nicht mit der vorgegebenen Stromstärke geladen werden{LimitingValue.CURRENT.value.format('Garage')}",
         id="begrenzt durch Strom"),
     pytest.param(
        6, LoadmanagementLimit(LimitingValue.POWER.value.format('Garage'), LimitingValue.POWER),
        f"Es kann nicht mit der vorgegebenen Stromstärke geladen werden{LimitingValue.POWER.value.format('Garage')}",
         id="begrenzt durch Leistung"),
     pytest.param(
        6, LoadmanagementLimit(LimitingValue.UNBALANCED_LOAD.value.format('Garage'), LimitingValue.UNBALANCED_LOAD),
        f"Es kann nicht mit der vorgegebenen Stromstärke geladen werden"
        f"{LimitingValue.UNBALANCED_LOAD.value.format('Garage')}",
        id="begrenzt durch Schieflast"),
     ])
def test_set_loadmangement_message(set_current, limit, expected_msg, monkeypatch):
    # setup
    ev = Ev(0)
    ev.charge_template = ChargeTemplate(0)
    cp1 = Chargepoint(1, None)
    cp1.data = ChargepointData(set=Set(current=set_current),
                               control_parameter=ControlParameter(required_currents=[8]*3))

    # execution
    additional_current.AdditionalCurrent()._set_loadmangement_message(7, limit, cp1)

    # evaluation
    assert cp1.data.get.state_str == expected_msg
