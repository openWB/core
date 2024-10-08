from dataclasses import dataclass
from unittest.mock import Mock
import pytest
from control.bat import Bat

from control.bat_all import BatAll
from control import data
from control.chargepoint.chargepoint_all import AllChargepointData, AllChargepoints, AllGet
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
    "parent, bat_power, pv_power, expected_power_hybrid",
    [
        pytest.param({"id": 6, "type": "counter", "children": [
            {"id": 2, "type": "bat", "children": []}]}, 100, -6400, (150, False),
            id="kein Hybrid-System, Speicher wird geladen"),
        pytest.param({"id": 6, "type": "counter", "children": [
            {"id": 2, "type": "bat", "children": []}]}, -100, -6400, (150, False),
            id="kein Hybrid-System, Speicher wird entladen"),
        pytest.param({"id": 1, "type": "inverter", "children": []}, 600, -6400, (800, True),
                     id="Speicher lädt mit 600W, max 800W bis WR max"),
        pytest.param({"id": 1, "type": "inverter", "children": []}, 600, -7200, (0, True),
                     id="maximale Entladeleistung des WR erreicht, Speicher lädt, keine Entladeleistung über"),
        pytest.param({"id": 1, "type": "inverter", "children": []}, -600, -6400, (200, True),
                     id="Speicher entlädt mit 600W, max 200W bis WR max"),
    ])
def test_max_bat_power_hybrid_system(parent, bat_power, pv_power, expected_power_hybrid, data_fixture, monkeypatch):
    # setup
    # pv1-Data: max_ac_out 7200
    mock_get_entry_of_parent = Mock(return_value=parent)
    monkeypatch.setattr(data.data.counter_all_data, "get_entry_of_parent", mock_get_entry_of_parent)
    data.data.pv_data["pv1"].data.get.power = pv_power

    b = BatAll()
    bat2 = Bat(2)
    bat2.data.get.power = bat_power

    # execution
    power = b._max_bat_power_hybrid_system(bat2)

    # evaluation
    assert power == expected_power_hybrid


@pytest.mark.parametrize(
    "required_power, return_max_bat_power_hybrid_system, expected_power",
    [
        pytest.param(1000, (1100, True), 1000, id="maximale Entladeleistung nicht erreicht"),
        pytest.param(1000, (900, True), 900, id="maximale Entladeleistung erreicht"),
        pytest.param(-1000, (10, True), -1000, id="Speicher soll nicht mehr entladen werden"),
        pytest.param(1000, (900, False), 1000, id="kein Hybrid-System"),
    ])
def test_limit_bat_power_discharge(required_power, return_max_bat_power_hybrid_system, expected_power, monkeypatch):
    # setup
    data.data.bat_data = {"bat2": Bat(2)}
    mock_max_bat_power_hybrid_system = Mock(return_value=return_max_bat_power_hybrid_system)
    monkeypatch.setattr(BatAll, "_max_bat_power_hybrid_system", mock_max_bat_power_hybrid_system)

    b = BatAll()

    # execution
    power = b._limit_bat_power_discharge(required_power)

    # evaluation
    assert power == expected_power


@ dataclass
class Params:
    name: str
    config: PvCharging
    power: float
    soc: float
    expected_charging_power_left: float
    expected_regulate_up: bool


cases = [
    Params("Speicher, Speicher lädt", PvCharging(bat_mode="bat_mode"), 500, 90, -100, True),
    Params("Speicher, Speicher entlädt", PvCharging(bat_mode="bat_mode"), -500, 90, -600, True),
    Params("Speicher, Speicher ist voll", PvCharging(bat_mode="bat_mode"), 0, 100, 0, False),
    Params("EV, Speicher lädt", PvCharging(bat_mode="ev_mode"), 500, 90, 500, False),
    Params("EV, Speicher entlädt", PvCharging(bat_mode="ev_mode"), -500, 90, -500, False),
    Params("EV, Speicher ist voll", PvCharging(bat_mode="ev_mode"), 0, 100, 0, False),
    Params("Mindest-SoC, SoC nicht erreicht, Speicher entlädt",
           PvCharging(bat_mode="min_soc_bat_mode"), -500, 40, -600, True),
    Params("Mindest-SoC, SoC nicht erreicht, Speicher lädt",
           PvCharging(bat_mode="min_soc_bat_mode"), 500, 40, -100, True),
    Params("Mindest-SoC, SoC nicht erreicht, Speicher-Reserve, Speicher entlädt",
           PvCharging(bat_mode="min_soc_bat_mode", bat_power_reserve=2000, bat_power_reserve_active=True),
           -500, 40, -600, True),
    Params("Mindest-SoC, SoC nicht erreicht, Speicher-Reserve nicht ausgenutzt, Speicher lädt",
           PvCharging(bat_mode="min_soc_bat_mode", bat_power_reserve=2000, bat_power_reserve_active=True),
           1600, 40, -500, True),
    Params("Mindest-SoC, SoC nicht erreicht, Speicher-Reserve ausgenutzt, Speicher lädt",
           PvCharging(bat_mode="min_soc_bat_mode", bat_power_reserve=2000, bat_power_reserve_active=True),
           2200, 40, 200, False),
    Params("Mindest-SoC, SoC erreicht, Speicher entlädt", PvCharging(bat_mode="min_soc_bat_mode"), -500, 90, -500,
           False),
    Params("Mindest-SoC, SoC erreicht, Speicher lädt", PvCharging(bat_mode="min_soc_bat_mode"), 500, 90, 500, False),
    Params("Mindest-SoC, SoC erreicht, Speicher ist voll", PvCharging(bat_mode="min_soc_bat_mode"), 0, 100, 0, False),
    Params("Mindest-SoC, SoC erreicht, Entladung in Auto, Speicher entlädt, Entladeleistung nicht erreicht",
           PvCharging(bat_mode="min_soc_bat_mode", bat_power_discharge=500, bat_power_discharge_active=True),
           -400, 90, 100, False),
    Params("Mindest-SoC, SoC erreicht, Entladung in Auto, Speicher entlädt, mehr als Entladeleistung",
           PvCharging(bat_mode="min_soc_bat_mode", bat_power_discharge=500, bat_power_discharge_active=True),
           -600, 90, -100, False),
    Params("Mindest-SoC, SoC erreicht, Entladung in Auto, Speicher entlädt, Entladeleistung erreicht",
           PvCharging(bat_mode="min_soc_bat_mode", bat_power_discharge=500, bat_power_discharge_active=True),
           -500, 90, 0, False),
    Params("Mindest-SoC, SoC erreicht, Entladung in Auto, Speicher lädt mit mehr als Entladeleistung",
           PvCharging(bat_mode="min_soc_bat_mode", bat_power_discharge=500, bat_power_discharge_active=True),
           650, 90, 1150, False),
    Params("Mindest-SoC, SoC erreicht, Entladung in Auto, Speicher lädt mit weniger als Entladeleistung",
           PvCharging(bat_mode="min_soc_bat_mode", bat_power_discharge=500, bat_power_discharge_active=True),
           400, 90, 900, False),
    Params("Mindest-SoC, SoC erreicht, Entladung in Auto, Speicher voll",
           PvCharging(bat_mode="min_soc_bat_mode", bat_power_reserve=500, bat_power_reserve_active=True,
                      min_bat_soc=100), 0, 100, 0, False),
]


@ pytest.mark.parametrize("params", cases, ids=[c.name for c in cases])
def test_get_charging_power_left(params: Params, caplog, data_fixture, monkeypatch):
    # setup
    b_all = BatAll()
    b_all.data.get.power = params.power
    b_all.data.get.soc = params.soc
    b = Bat(0)
    b.data.get.power = params.power
    data.data.bat_data["bat0"] = b
    data.data.general_data.data.chargemode_config.pv_charging = params.config
    mock__max_bat_power_hybrid_system = Mock(return_value=(params.power, None))
    monkeypatch.setattr(BatAll, "_max_bat_power_hybrid_system", mock__max_bat_power_hybrid_system)

    # execution
    b_all._get_charging_power_left()

    # evaluation
    assert b_all.data.set.charging_power_left == params.expected_charging_power_left
    assert b_all.data.set.regulate_up == params.expected_regulate_up
