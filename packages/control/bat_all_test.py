from dataclasses import dataclass
from unittest.mock import Mock
import pytest

from control.bat_all import BatAll, SwitchOnBatState
from control import data
from control.chargepoint import AllChargepointData, AllChargepoints, AllGet
from control.general import General, PvCharging


@pytest.fixture
def data_fixture() -> None:
    data.data_init(Mock())
    data.data.general_data = General()
    data.data.cp_all_data = Mock(spec=AllChargepoints, data=Mock(
        spec=AllChargepointData, get=Mock(spec=AllGet, power=0)))


@dataclass
class Params:
    name: str
    config: PvCharging
    soc: float
    expected_charging_power_left: float


cases = [
    Params("Speicher-Vorrang ohne Ladeleistungsreserve", PvCharging(bat_prio=False, charging_power_reserve=0),
           100, 500),
    Params("Speicher-Vorrang mit Ladeleistungsreserve", PvCharging(bat_prio=False, charging_power_reserve=200),
           100, 300),
    Params("EV-Vorrang mit erlaubter Entladeleistung", PvCharging(bat_prio=True), 51, 1000),
    Params("EV-Vorrang ohne erlaubte Entladeleistung", PvCharging(bat_prio=True), 50, -50),
]


@pytest.mark.parametrize("params", cases, ids=[c.name for c in cases])
def test_get_charging_power_left(params: Params, caplog, data_fixture):
    # setup
    b = BatAll()
    b.data.get.power = 500
    b.data.get.soc = params.soc
    data.data.general_data.data.chargemode_config.pv_charging = params.config

    # execution
    b._get_charging_power_left()

    # evaluation
    assert b.data.set.charging_power_left == params.expected_charging_power_left


@pytest.mark.parametrize(
    "soc, switch_on_soc_reached, switch_on_soc, switch_off_soc," +
    "expected_switch_on_soc_state, expected_switch_on_soc_reached",
    [pytest.param(41, True, 60, 40, SwitchOnBatState.CHARGE_FROM_BAT, True,
                  id="Laderegelung freigegeben, Ausschalt-SoC nicht erreicht"),
     pytest.param(60, True, 60, 0, SwitchOnBatState.REACH_ONLY_SWITCH_ON_SOC, True,
                  id="Laderegelung freigegeben, Ausschalt-SoC nicht konfiguriert"),
     pytest.param(40, True, 60, 40, SwitchOnBatState.SWITCH_OFF_SOC_REACHED, False,
                  id="Laderegelung freigegeben, Ausschalt-SoC erreicht"),
     pytest.param(40, False, 0, 40, SwitchOnBatState.SWITCH_OFF_SOC_REACHED, False,
                  id="Laderegelung nicht freigegeben, Einschalt-SoC nicht konfiguriert, Ausschalt-SoC erreicht"),
     pytest.param(41, False, 0, 40, SwitchOnBatState.CHARGE_FROM_BAT, True,
                  id="Laderegelung nicht freigegeben, Einschalt-SoC nicht konfiguriert, Ausschalt-SoC nicht erreicht"),
     pytest.param(60, False, 60, 40, SwitchOnBatState.CHARGE_FROM_BAT, True,
                  id="Laderegelung nicht freigegeben, Einschalt-SoC erreicht"),
     pytest.param(59, False, 60, 40, SwitchOnBatState.SWITCH_ON_SOC_NOT_REACHED, False,
                  id="Laderegelung nicht freigegeben, Einschalt-SoC nicht erreicht")]

)
def test_get_switch_on_state(soc: float,
                             switch_on_soc_reached: bool,
                             switch_on_soc: int,
                             switch_off_soc: int,
                             expected_switch_on_soc_state: SwitchOnBatState,
                             expected_switch_on_soc_reached: bool):
    # setup
    b = BatAll()
    b.data.get.soc = soc
    b.data.set.switch_on_soc_reached = switch_on_soc_reached
    data.data.general_data.data.chargemode_config.pv_charging.switch_on_soc = switch_on_soc
    data.data.general_data.data.chargemode_config.pv_charging.switch_off_soc = switch_off_soc

    # execution
    b._get_switch_on_state()

    # evaluation
    assert b.data.set.switch_on_soc_reached == expected_switch_on_soc_reached
    assert b.data.set.switch_on_soc_state == expected_switch_on_soc_state
