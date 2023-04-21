from dataclasses import dataclass
from unittest.mock import Mock
import pytest
from control.bat import Bat

from control.bat_all import BatAll, SwitchOnBatState
from control import data
from control.chargepoint import AllChargepointData, AllChargepoints, AllGet
from control.general import General, PvCharging
from control.pv import Config, Get, Pv, PvData


@pytest.fixture
def data_fixture() -> None:
    data.data_init(Mock())
    data.data.general_data = General()
    data.data.cp_all_data = Mock(spec=AllChargepoints, data=Mock(
        spec=AllChargepointData, get=Mock(spec=AllGet, power=0)))
    data.data.pv_data["pv1"] = Mock(spec=Pv, data=Mock(spec=PvData, get=Mock(spec=Get, power=-6400),
                                                       config=Mock(spec=Config, max_ac_out=7200)))


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
                  id="Laderegelung nicht freigegeben, Einschalt-SoC nicht erreicht"),
     pytest.param(59, False, 0, 0, SwitchOnBatState.CHARGE_FROM_BAT, True,
                  id="Ein/Ausschalt-SoC nicht konfiguriert")]

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


@pytest.mark.parametrize("parent, bat_power, expected_power",
                         [
                             pytest.param({"id": 6, "type": "counter", "children": [
                                          {"id": 2, "type": "bat", "children": []}]}, 100, 150,
                                          id="kein Hybrid-System, Speicher wird geladen"),
                             pytest.param({"id": 6, "type": "counter", "children": [
                                          {"id": 2, "type": "bat", "children": []}]}, -100, 150,
                                          id="kein Hybrid-System, Speicher wird entladen"),
                             pytest.param({"id": 1, "type": "inverter", "children": []}, 600, 800,
                                          id="maximale Entladeleistung des WR"),
                         ])
def test_max_bat_power_hybrid_system(parent, bat_power, expected_power, data_fixture, monkeypatch):
    # setup
    # pv1-Data: max_ac_out 7200, power 6400
    mock_get_entry_of_parent = Mock(return_value=parent)
    monkeypatch.setattr(data.data.counter_all_data, "get_entry_of_parent", mock_get_entry_of_parent)

    b = BatAll()
    bat2 = Bat(2)
    bat2.data.get.power = bat_power

    # execution
    power = b._max_bat_power_hybrid_system(bat2)

    # evaluation
    assert power == expected_power


@pytest.mark.parametrize("return_max_bat_power_hybrid_system, expected_power",
                         [
                             pytest.param(1100, 1000,
                                          id="maximale Entladeleistung erreicht"),
                             pytest.param(900, 900,
                                          id="maximale Entladeleistung nicht erreicht/ kein Hybrid-System"),
                         ])
def test_limit_rundown_power(return_max_bat_power_hybrid_system, expected_power, monkeypatch):
    # setup
    data.data.bat_data = {"bat2": Bat(2)}
    mock_max_bat_power_hybrid_system = Mock(return_value=return_max_bat_power_hybrid_system)
    monkeypatch.setattr(BatAll, "_max_bat_power_hybrid_system", mock_max_bat_power_hybrid_system)

    b = BatAll()

    # execution
    power = b._limit_rundown_power(1000)

    # evaluation
    assert power == expected_power


@ dataclass
class Params:
    name: str
    config: PvCharging
    soc: float
    expected_charging_power_left: float


cases = [
    Params("EV-Vorrang ohne Ladeleistungsreserve", PvCharging(bat_prio=False, charging_power_reserve=0),
           100, 500),
    Params("EV-Vorrang mit Ladeleistungsreserve, Speicher voll",
           PvCharging(bat_prio=False, charging_power_reserve=200),
           100, 500),
    Params("EV-Vorrang mit Ladeleistungsreserve", PvCharging(bat_prio=False, charging_power_reserve=200),
           99, 300),
    Params("Speicher-Vorrang mit erlaubter Entladeleistung", PvCharging(bat_prio=True), 51, 500),
    Params("Speicher-Vorrang ohne erlaubte Entladeleistung, Minimal-SoC überschritten",
           PvCharging(bat_prio=True), 50, -50),
]


@ pytest.mark.parametrize("params", cases, ids=[c.name for c in cases])
def test_get_charging_power_left(params: Params, caplog, data_fixture, monkeypatch):
    # setup
    b_all = BatAll()
    b_all.data.get.power = 500
    b_all.data.get.soc = params.soc
    b = Bat(0)
    b.data.get.power = 500
    data.data.bat_data["bat0"] = b
    data.data.general_data.data.chargemode_config.pv_charging = params.config
    mock__max_bat_power_hybrid_system = Mock(return_value=500)
    monkeypatch.setattr(BatAll, "_max_bat_power_hybrid_system", mock__max_bat_power_hybrid_system)

    # execution
    b_all._get_charging_power_left()

    # evaluation
    assert b_all.data.set.charging_power_left == params.expected_charging_power_left
