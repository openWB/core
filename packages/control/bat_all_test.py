from dataclasses import dataclass, field
from typing import List, Optional
from unittest.mock import MagicMock, Mock
import pytest
from packages.conftest import hierarchy_standard
from control import bat_all
from control.bat import Bat

from control.bat_all import BatAll, BatPowerLimitMode, BatPowerLimitCondition
from control import data
from control.chargepoint.chargepoint import Chargepoint
from control.chargepoint.chargepoint_all import AllChargepointData, AllChargepoints, AllGet
from control.general import General, PvCharging
from control.pv import Config, Get, Pv, PvData
from modules.devices.generic.mqtt.bat import MqttBat
from modules.devices.generic.mqtt.config import MqttBatSetup


@pytest.fixture
def data_fixture() -> None:
    data.data_init(Mock())
    data.data.general_data = General()
    data.data.cp_all_data = Mock(spec=AllChargepoints, data=Mock(
        spec=AllChargepointData, get=Mock(spec=AllGet, power=0)))
    data.data.pv_data["pv1"] = Mock(spec=Pv, data=Mock(spec=PvData, get=Mock(spec=Get, power=-6400),
                                                       config=Mock(spec=Config, max_ac_out=7200)))


@pytest.mark.parametrize(
    "max_ac_out, power, expected_result",
    [
        pytest.param(5000, -6000, 1000, id="Leistung überschreitet max_ac_out"),
        pytest.param(5000, -4000, 0, id="Leistung liegt unter max_ac_out"),
        pytest.param(5000, 0, 0, id="Keine Leistung (power = 0)"),
        pytest.param(0, -6000, 0, id="max_ac_out ist 0"),
    ],
)
def test_inverter_limited_power(max_ac_out, power, expected_result):
    # Mock für die Pv-Klasse
    inverter = Pv(1)
    inverter.data.config.max_ac_out = max_ac_out
    inverter.data.get.power = power
    bat_all = BatAll()

    # Aufruf der zu testenden Funktion
    result = bat_all._inverter_limited_power(inverter)

    # Überprüfung des Ergebnisses
    assert result == expected_result


@pytest.mark.parametrize(
    "required_power, return_inverter_limited_power, expected_power",
    [
        pytest.param(1000, 0, 1000, id="maximale Entladeleistung nicht erreicht"),
        pytest.param(1000, 100, 900, id="maximale Entladeleistung erreicht"),
        pytest.param(-1000, 10, -1000, id="Speicher soll nicht mehr entladen werden"),
    ])
def test_limit_bat_power_discharge(required_power, return_inverter_limited_power, expected_power, monkeypatch):
    # setup
    data.data.pv_data = {"pv2": Pv(2)}
    mock_inverter_limited_power = Mock(return_value=return_inverter_limited_power)
    monkeypatch.setattr(BatAll, "_inverter_limited_power", mock_inverter_limited_power)

    b = BatAll()

    # execution
    power = b._limit_bat_power_discharge(required_power)

    # evaluation
    assert power == expected_power


@dataclass
class Params:
    name: str
    config: PvCharging
    power: float
    soc: float
    expected_charging_power_left: float
    expected_regulate_up: bool
    power_limit: Optional[float] = None


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
    Params(("Mindest-SoC, SoC erreicht, Entladung in Auto, Speicher lädt mit weniger als Entladeleistung, "
           "Speicher-Sperre aktiv"),
           PvCharging(bat_mode="min_soc_bat_mode", bat_power_discharge=500, bat_power_discharge_active=True),
           400, 90, 0, False, 600),
]


@pytest.mark.parametrize("params", cases, ids=[c.name for c in cases])
def test_get_charging_power_left(params: Params, caplog, data_, monkeypatch):
    # setup
    b_all = BatAll()
    b_all.data.get.power = params.power
    b_all.data.get.soc = params.soc
    b_all.data.set.power_limit = params.power_limit
    b = Bat(0)
    b.data.get.power = params.power
    data.data.bat_data["bat0"] = b
    data.data.general_data.data.chargemode_config.pv_charging = params.config
    mock_limit_bat_power_discharge = MagicMock(side_effect=lambda x: x)
    monkeypatch.setattr(BatAll, "_limit_bat_power_discharge", mock_limit_bat_power_discharge)

    # execution
    b_all._get_charging_power_left()

    # evaluation
    assert b_all.data.set.charging_power_left == params.expected_charging_power_left
    assert b_all.data.set.regulate_up == params.expected_regulate_up


def default_chargepoint_factory() -> List[Chargepoint]:
    cp = Chargepoint(3, None)
    cp.data.get.power = 1400
    return [cp]


@dataclass
class PowerLimitParams:
    name: str
    expected_power_limit_bat: Optional[float]
    power_limit_mode: str = BatPowerLimitMode.MODE_NO_DISCHARGE.value
    power_limit_condition: str = BatPowerLimitCondition.VEHICLE_CHARGING.value
    cps: List[Chargepoint] = field(default_factory=default_chargepoint_factory)
    power_limit_controllable: bool = True
    bat_power: float = -10
    evu_power: float = 200
    bat_control_activated: bool = True


cases = [
    PowerLimitParams("Begrenzung immer, Speicher nicht regelbar", None, power_limit_controllable=False,
                     power_limit_mode=BatPowerLimitMode.MODE_NO_DISCHARGE.value),
    PowerLimitParams("Begrenzung immer, Speichersteuerung deaktiviert", None, bat_control_activated=False,
                     power_limit_mode=BatPowerLimitMode.MODE_NO_DISCHARGE.value),
    PowerLimitParams("Begrenzung immer, keine LP im Sofortladen", None, cps=[],
                     power_limit_mode=BatPowerLimitMode.MODE_NO_DISCHARGE.value),
    PowerLimitParams("Begrenzung immer, Speicher lädt", None, bat_power=100,
                     power_limit_mode=BatPowerLimitMode.MODE_NO_DISCHARGE.value),
    PowerLimitParams("Begrenzung immer,Einspeisung", None, evu_power=-110,
                     power_limit_mode=BatPowerLimitMode.MODE_NO_DISCHARGE.value),
    PowerLimitParams("Begrenzung immer", 0, power_limit_mode=BatPowerLimitMode.MODE_NO_DISCHARGE.value),
    PowerLimitParams("Begrenzung Hausverbrauch", -456,
                     power_limit_mode=BatPowerLimitMode.MODE_DISCHARGE_HOME_CONSUMPTION.value),
]


@pytest.mark.parametrize("params", cases, ids=[c.name for c in cases])
def test_get_power_limit(params: PowerLimitParams, data_, monkeypatch):
    b_all = BatAll()
    b_all.data.config.bat_control_permitted = True
    b_all.data.config.bat_control_activated = params.bat_control_activated
    b_all.data.config.power_limit_mode = params.power_limit_mode
    b_all.data.config.power_limit_condition = params.power_limit_condition
    b_all.data.get.power_limit_controllable = params.power_limit_controllable
    b_all.data.get.power = params.bat_power
    data.data.counter_all_data = hierarchy_standard()
    data.data.counter_all_data.data.set.home_consumption = 456
    data.data.cp_all_data.data.get.power = 1400
    data.data.counter_data["counter0"].data.get.power = params.evu_power
    data.data.bat_all_data = b_all

    get_chargepoints_by_chargemodes_mock = Mock(return_value=params.cps)
    monkeypatch.setattr(bat_all, "get_chargepoints_by_chargemodes", get_chargepoints_by_chargemodes_mock)
    get_evu_counter_mock = Mock(return_value=data.data.counter_data["counter0"])
    monkeypatch.setattr(data.data.counter_all_data, "get_evu_counter", get_evu_counter_mock)
    get_controllable_bat_components_mock = Mock(return_value=[MqttBat(MqttBatSetup(id=2), device_id=0)])
    monkeypatch.setattr(bat_all, "get_controllable_bat_components", get_controllable_bat_components_mock)

    data.data.bat_all_data.get_power_limit()

    assert data.data.bat_data["bat2"].data.set.power_limit == params.expected_power_limit_bat
