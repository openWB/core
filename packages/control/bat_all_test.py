from dataclasses import dataclass
from typing import List, Optional
from unittest.mock import MagicMock, Mock
import pytest
from packages.conftest import hierarchy_standard
from control import bat_all
from control.bat import Bat

from control.bat_all import BatAll, BatConsiderationMode, BatPowerLimitMode, BatPowerLimitCondition, ManualMode
from control import data
from control.chargepoint.chargepoint import Chargepoint
from control.chargepoint.chargepoint_all import AllChargepointData, AllChargepoints, AllGet
from control.general import ChargemodeConfigBat, General
from control.pv import Config, Get, Pv, PvData
from modules.devices.generic.mqtt.bat import MqttBat
from modules.devices.generic.mqtt.config import MqttBatSetup


@pytest.fixture(autouse=True)
def data_fixture() -> None:
    data.data_init(Mock())
    data.data.general_data = General()
    data.data.cp_all_data = Mock(spec=AllChargepoints, data=Mock(
        spec=AllChargepointData, get=Mock(spec=AllGet, power=0)))
    data.data.pv_data["pv1"] = Mock(spec=Pv, data=Mock(spec=PvData, get=Mock(spec=Get, power=-6400),
                                                       config=Mock(spec=Config, max_ac_out=7200)))


@pytest.mark.parametrize(
    "bat_power, pv_power, expected_power",
    [
        pytest.param(-1000, 0, 4000, id="Leistung verfügbar"),
        pytest.param(-4900, -100, 0, id="max Leistung des WR um 100W überschritten, Speicher entlädt"),
        pytest.param(1000, -4500, 500, id="Speicher lädt, soll entladen"),
    ])
def test_get_charging_power_left_diff_hybrid(bat_power: int,
                                             pv_power: int,
                                             expected_power: int,
                                             monkeypatch: pytest.MonkeyPatch):
    # setup
    data.data.pv_data = {"pv2": Pv(2)}
    data.data.pv_data["pv2"].data.get.power = pv_power
    data.data.pv_data["pv2"].data.config.max_ac_out = 5000
    data.data.bat_data["bat1"] = Bat(1)
    data.data.bat_data["bat1"].data.get.power = bat_power
    data.data.bat_data["bat1"].data.get.soc = 71
    data.data.general_data.data.chargemode_config.bat.mode = BatConsiderationMode.MIN_SOC_BAT.value
    data.data.general_data.data.chargemode_config.bat.power_discharge = 5000
    data.data.general_data.data.chargemode_config.bat.power_discharge_active = True
    monkeypatch.setattr(data.data.counter_all_data, "get_hybrid_bat_ids", Mock(return_value=[1]))
    monkeypatch.setattr(data.data.counter_all_data, "get_non_hybrid_bat_ids", Mock(return_value=[]))
    monkeypatch.setattr(data.data.counter_all_data, "get_hybrid_inverter_ids", Mock(return_value=[2]))

    b_all = BatAll()
    b_all.data.get.power = bat_power
    b_all.data.get.soc = 71

    # execution
    b_all.get_charging_power_left_diff()

    # evaluation
    assert b_all.data.set.charging_power_left == expected_power


@pytest.mark.parametrize(
    "hybrid_bat_ids, non_hybrid_bat_ids, hybrid_inverter_ids, expected_power",
    [
        pytest.param([], [1], [], float("inf"), id="no hybrid"),
        pytest.param([1], [], [2], 4900, id="hybrid,"),
        pytest.param([1], [3], [2], 10900, id="hybrid an non hybrid bat"),
    ])
def test__absolute_bat_discharge_power(hybrid_bat_ids: List[int],
                                       non_hybrid_bat_ids: List[int],
                                       hybrid_inverter_ids: List[int],
                                       expected_power: float,
                                       monkeypatch: pytest.MonkeyPatch):
    # setup
    data.data.pv_data = {"pv2": Pv(2)}
    data.data.pv_data["pv2"].data.get.power = -100
    data.data.pv_data["pv2"].data.config.max_ac_out = 5000
    data.data.bat_data["bat1"] = Bat(1)
    data.data.bat_data["bat1"].data.get.power = -4900
    data.data.bat_data["bat3"] = Bat(3)
    data.data.bat_data["bat3"].data.get.max_discharge_power = 6000
    monkeypatch.setattr(data.data.counter_all_data, "get_hybrid_bat_ids", Mock(return_value=hybrid_bat_ids))
    monkeypatch.setattr(data.data.counter_all_data, "get_non_hybrid_bat_ids", Mock(return_value=non_hybrid_bat_ids))
    monkeypatch.setattr(data.data.counter_all_data, "get_hybrid_inverter_ids", Mock(return_value=hybrid_inverter_ids))

    b = BatAll()
    b.data.get.power = -4900

    # execution
    power = b._absolute_bat_discharge_power()  # pyright: ignore[reportPrivateUsage]

    # evaluation
    assert power == expected_power


@dataclass
class Params:
    name: str
    config: ChargemodeConfigBat
    power: float
    soc: float
    expected_charging_power_left: float
    expected_regulate_up: bool
    power_limit: Optional[float] = None
    hysteresis_discharge: bool = False


cases = [
    Params("Speicher, Speicher lädt", ChargemodeConfigBat(mode="bat_mode"), 500, 90, -100, True),
    Params("Speicher, Speicher entlädt", ChargemodeConfigBat(mode="bat_mode"), -500, 90, -600, True),
    Params("Speicher, Speicher ist voll", ChargemodeConfigBat(mode="bat_mode"), 0, 100, 0, False),
    Params("EV, Speicher lädt", ChargemodeConfigBat(mode="ev_mode"), 500, 90, 500, False),
    Params("EV, Speicher entlädt", ChargemodeConfigBat(mode="ev_mode"), -500, 90, -500, False),
    Params("EV, Speicher ist voll", ChargemodeConfigBat(mode="ev_mode"), 0, 100, 0, False),
    Params("Mindest-SoC, SoC nicht erreicht, Speicher entlädt",
           ChargemodeConfigBat(mode="min_soc_bat_mode"), -500, 40, -600, True),
    Params("Mindest-SoC, SoC nicht erreicht, Speicher lädt",
           ChargemodeConfigBat(mode="min_soc_bat_mode"), 500, 40, -100, True),
    Params("Mindest-SoC, SoC nicht erreicht, Speicher-Reserve, Speicher entlädt",
           ChargemodeConfigBat(mode="min_soc_bat_mode", power_reserve=2000, power_reserve_active=True),
           -500, 40, -600, True),
    Params("Mindest-SoC, SoC nicht erreicht, Speicher-Reserve nicht ausgenutzt, Speicher lädt",
           ChargemodeConfigBat(mode="min_soc_bat_mode", power_reserve=2000, power_reserve_active=True),
           1600, 40, -500, True),
    Params("Mindest-SoC, SoC nicht erreicht, Speicher-Reserve ausgenutzt, Speicher lädt",
           ChargemodeConfigBat(mode="min_soc_bat_mode", power_reserve=2000, power_reserve_active=True),
           2200, 40, 200, False),
    Params("Mindest-SoC, SoC erreicht, Speicher entlädt", ChargemodeConfigBat(mode="min_soc_bat_mode"), -500, 90, -500,
           False),
    Params("Mindest-SoC, SoC erreicht, Speicher lädt",
           ChargemodeConfigBat(mode="min_soc_bat_mode"), 500, 90, 500, False),
    Params("Mindest-SoC, SoC erreicht, Speicher ist voll",
           ChargemodeConfigBat(mode="min_soc_bat_mode"), 0, 100, 0, False),
    Params("Mindest-SoC, SoC erreicht, Entladung in Auto, Speicher entlädt, Entladeleistung nicht erreicht",
           ChargemodeConfigBat(mode="min_soc_bat_mode", power_discharge=500, power_discharge_active=True),
           -400, 90, 100, False),
    Params("Mindest-SoC, SoC erreicht, Entladung in Auto, Speicher entlädt, mehr als Entladeleistung",
           ChargemodeConfigBat(mode="min_soc_bat_mode", power_discharge=500, power_discharge_active=True),
           -600, 90, -100, False),
    Params("Mindest-SoC, SoC erreicht, Entladung in Auto, Speicher entlädt, Entladeleistung erreicht",
           ChargemodeConfigBat(mode="min_soc_bat_mode", power_discharge=500, power_discharge_active=True),
           -500, 90, 0, False),
    Params("Mindest-SoC, SoC erreicht, Entladung in Auto, Speicher lädt mit mehr als Entladeleistung",
           ChargemodeConfigBat(mode="min_soc_bat_mode", power_discharge=500, power_discharge_active=True),
           650, 90, 1150, False),
    Params("Mindest-SoC, SoC erreicht, Entladung in Auto, Speicher lädt mit weniger als Entladeleistung",
           ChargemodeConfigBat(mode="min_soc_bat_mode", power_discharge=500, power_discharge_active=True),
           400, 90, 900, False),
    Params("Mindest-SoC, SoC erreicht, Entladung in Auto, Speicher voll",
           ChargemodeConfigBat(mode="min_soc_bat_mode", power_reserve=500, power_reserve_active=True,
                               min_soc=100), 0, 100, 0, False),
    Params(("Mindest-SoC, SoC erreicht, Entladung in Auto, Speicher lädt mit weniger als Entladeleistung, "
           "Speicher-Sperre aktiv"),
           ChargemodeConfigBat(mode="min_soc_bat_mode", power_discharge=500, power_discharge_active=True),
           400, 90, 0, False, 600),
    Params(("Mindest-SoC, Hysterese, EV-Vorrang, keine Speichernutzung"),
           ChargemodeConfigBat(mode="min_soc_bat_mode"), 400, 60, 400, False, hysteresis_discharge=False),
    Params(("Mindest-SoC, Hysterese, Speicherentladung, Speichernutzung erlaubt"),
           ChargemodeConfigBat(mode="min_soc_bat_mode", power_discharge=500, power_discharge_active=True),
           400, 60, 900, False, hysteresis_discharge=True),
    Params(("Mindest-SoC, Hysterese, Speicherentladung, Speichernutzung erlaubt, Speicher-Sperre aktiv"),
           ChargemodeConfigBat(mode="min_soc_bat_mode", power_discharge=500, power_discharge_active=True),
           400, 60, 0, False, 600, hysteresis_discharge=True),
]


@pytest.mark.parametrize("params", cases, ids=[c.name for c in cases])
def test_get_charging_power_left(params: Params, data_, monkeypatch: pytest.MonkeyPatch):
    # setup
    b_all = BatAll()
    b_all.data.get.power = params.power
    b_all.data.get.soc = params.soc
    b_all.data.set.power_limit = params.power_limit
    b_all.data.set.hysteresis_discharge = params.hysteresis_discharge
    b = Bat(0)
    b.data.get.power = params.power
    data.data.bat_data["bat0"] = b
    data.data.general_data.data.chargemode_config.bat = params.config
    mock_absolute_bat_discharge_power = MagicMock(return_value=10000)
    monkeypatch.setattr(BatAll, "_absolute_bat_discharge_power", mock_absolute_bat_discharge_power)

    # execution
    b_all.get_charging_power_left_diff()

    # evaluation
    assert b_all.data.set.charging_power_left == params.expected_charging_power_left
    assert b_all.data.set.regulate_up == params.expected_regulate_up


def test_get_charging_power_left_uses_limited_bat_discharge_in_hysteresis(
        data_: data.Data, monkeypatch: pytest.MonkeyPatch):
    # setup: min/max-SoC-Bereich mit aktiver Hysterese und erlaubter Entladeleistung
    b_all = BatAll()
    b_all.data.get.power = -2500
    b_all.data.get.soc = 60
    b_all.data.set.hysteresis_discharge = True
    b_all.data.set.power_limit = None
    data.data.general_data.data.chargemode_config.bat = ChargemodeConfigBat(
        mode="min_soc_bat_mode",
        min_soc=40,
        max_soc=80,
        power_discharge=8000,
        power_discharge_active=True,
    )

    # Hybrid-Setup fuer reale Berechnung in _limit_bat_power_discharge
    data.data.pv_data = {"pv2": Pv(2)}
    data.data.pv_data["pv2"].data.get.power = -7500
    data.data.pv_data["pv2"].data.config.max_ac_out = 10000
    data.data.bat_data["bat1"] = Bat(1)
    data.data.bat_data["bat1"].data.get.power = -2500
    monkeypatch.setattr(data.data.counter_all_data, "get_hybrid_bat_ids", Mock(return_value=[1]))
    monkeypatch.setattr(data.data.counter_all_data, "get_non_hybrid_bat_ids", Mock(return_value=[]))
    monkeypatch.setattr(data.data.counter_all_data, "get_hybrid_inverter_ids", Mock(return_value=[2]))

    # execution
    b_all.get_charging_power_left_diff()

    # evaluation: reale Begrenzung (300W) + base_power (400W)
    assert b_all.data.set.charging_power_left == 0
    assert b_all.data.set.regulate_up is False


def default_chargepoint_factory() -> List[Chargepoint]:
    cp = Chargepoint(3, None)
    cp.data.get.power = 1400
    return [cp]


@dataclass
class BatControlParams:
    name: str
    expected_power_limit_bat: Optional[float]
    power_limit_mode: BatPowerLimitMode = BatPowerLimitMode.MODE_NO_DISCHARGE
    power_limit_condition: BatPowerLimitCondition = BatPowerLimitCondition.VEHICLE_CHARGING
    bat_manual_mode: ManualMode = ManualMode.MANUAL_DISABLE
    power_limit_controllable: bool = True
    bat_power: float = -10
    bat_soc: float = 50.0
    evu_power: float = 200
    pv_power: float = -654
    bat_control_permitted: bool = True
    bat_control_activated: bool = True
    max_charge_power: float = 5000
    max_discharge_power: float = -5000
    bat_control_min_soc: int = 10
    bat_control_max_soc: int = 90
    price_limit_activated: bool = False
    price_charge_activated: bool = False
    price_limit: float = 0.30
    charge_limit: float = 0.30


cases = [
    BatControlParams("Speicher nicht regelbar", None, power_limit_controllable=False,
                     power_limit_mode=BatPowerLimitMode.MODE_NO_DISCHARGE),
    BatControlParams("Disclaimer nicht akzeptiert", None, bat_control_permitted=False,
                     power_limit_mode=BatPowerLimitMode.MODE_NO_DISCHARGE),
    BatControlParams("Speichersteuerung deaktiviert", None, bat_control_activated=False,
                     power_limit_mode=BatPowerLimitMode.MODE_NO_DISCHARGE),
    # Manuelle Steuerung
    BatControlParams("Manuelle Steuerung, Speichersteuerung deaktiviert", None,
                     power_limit_condition=BatPowerLimitCondition.MANUAL,
                     bat_manual_mode=ManualMode.MANUAL_DISABLE),
    BatControlParams("Manuelle Steuerung, Entladung sperren", 0,
                     power_limit_condition=BatPowerLimitCondition.MANUAL,
                     bat_manual_mode=ManualMode.MANUAL_LIMIT),
    BatControlParams("Manuelle Steuerung, Begrenzung Hausverbrauch", -456,
                     power_limit_condition=BatPowerLimitCondition.MANUAL,
                     bat_manual_mode=ManualMode.MANUAL_LIMIT,
                     power_limit_mode=BatPowerLimitMode.MODE_DISCHARGE_HOME_CONSUMPTION),
    BatControlParams("Manuelle Steuerung, Ladung PV Überschuss", 198,
                     power_limit_condition=BatPowerLimitCondition.MANUAL,
                     bat_manual_mode=ManualMode.MANUAL_LIMIT,
                     power_limit_mode=BatPowerLimitMode.MODE_CHARGE_PV_PRODUCTION),
    BatControlParams("Manuelle Steuerung, Aktive Ladung", 5000,
                     power_limit_condition=BatPowerLimitCondition.MANUAL,
                     bat_manual_mode=ManualMode.MANUAL_CHARGE),
    # Wenn Fahrzeuge Laden
    BatControlParams("Fahrzeuge laden, Begrenzung immer, Speicher lädt", None, bat_power=100,
                     power_limit_mode=BatPowerLimitMode.MODE_NO_DISCHARGE),
    BatControlParams("Fahrzeuge laden, Begrenzung immer,Einspeisung", None, evu_power=-110,
                     power_limit_mode=BatPowerLimitMode.MODE_NO_DISCHARGE),
    BatControlParams("Fahrzeuge laden, Begrenzung immer", 0,
                     power_limit_mode=BatPowerLimitMode.MODE_NO_DISCHARGE),
    BatControlParams("Fahrzeuge laden, Begrenzung Hausverbrauch", -456,
                     power_limit_mode=BatPowerLimitMode.MODE_DISCHARGE_HOME_CONSUMPTION),
    BatControlParams("Fahrzeuge laden, Ladung PV Überschuss", 198,
                     power_limit_mode=BatPowerLimitMode.MODE_CHARGE_PV_PRODUCTION),
    BatControlParams("Fahrzeuge laden, Ladung PV Überschuss, Eigenverbrauch PV-Anlage", -456,
                     power_limit_mode=BatPowerLimitMode.MODE_CHARGE_PV_PRODUCTION,
                     pv_power=100),
]


@pytest.mark.parametrize("params", cases, ids=[c.name for c in cases])
def test_active_bat_control(params: BatControlParams, data_, monkeypatch: pytest.MonkeyPatch):
    b_all = BatAll()
    b_all.data.config.bat_control_activated = params.bat_control_activated
    b_all.data.config.power_limit_mode = params.power_limit_mode
    b_all.data.config.power_limit_condition = params.power_limit_condition
    b_all.data.config.manual_mode = params.bat_manual_mode
    b_all.data.get.power_limit_controllable = params.power_limit_controllable
    b_all.data.config.bat_control_min_soc = params.bat_control_min_soc
    b_all.data.config.bat_control_max_soc = params.bat_control_max_soc
    b_all.data.config.price_limit_activated = params.price_limit_activated
    b_all.data.config.price_charge_activated = params.price_charge_activated
    b_all.data.config.price_limit = params.price_limit
    b_all.data.config.charge_limit = params.charge_limit

    b_all.data.get.power = params.bat_power
    # b_all.data.get.soc = 50.0
    data.data.counter_all_data = hierarchy_standard()
    data.data.counter_all_data.data.set.home_consumption = 456
    data.data.pv_all_data.data.get.power = params.pv_power
    data.data.cp_all_data.data.get.power = 1400
    data.data.counter_data["counter0"].data.get.power = params.evu_power
    data.data.bat_all_data = b_all

    get_evu_counter_mock = Mock(return_value=data.data.counter_data["counter0"])
    monkeypatch.setattr(data.data.counter_all_data, "get_evu_counter", get_evu_counter_mock)
    get_bat_components_by_controllability_mock = Mock(return_value=([MqttBat(MqttBatSetup(id=2), device_id=0)], []))
    data.data.bat_data["bat2"].data.get.soc = params.bat_soc
    data.data.bat_data["bat2"].data.get.max_charge_power = params.max_charge_power
    data.data.bat_data["bat2"].data.get.max_discharge_power = params.max_discharge_power
    monkeypatch.setattr(bat_all, "get_bat_components_by_controllability",
                        get_bat_components_by_controllability_mock)

    data.data.bat_all_data.get_power_limit()
    data.data.bat_all_data._set_bat_power_active_control(data.data.bat_all_data.data.set.power_limit)

    assert data.data.bat_data["bat2"].data.set.power_limit == params.expected_power_limit_bat


cases = [
    # Nach Preisgrenze
    BatControlParams("Preisgrenze, Grenze deaktiviert, Eigenregelung", None,
                     power_limit_condition=BatPowerLimitCondition.PRICE_LIMIT,
                     price_limit_activated=False,
                     price_limit=0.40,
                     power_limit_mode=BatPowerLimitMode.MODE_NO_DISCHARGE),
    BatControlParams("Preisgrenze, Entladung sperren, Grenze unterschritten", 0,
                     power_limit_condition=BatPowerLimitCondition.PRICE_LIMIT,
                     price_limit_activated=True,
                     price_limit=0.30,
                     power_limit_mode=BatPowerLimitMode.MODE_NO_DISCHARGE),
    BatControlParams("Preisgrenze, Überschuss Laden, Grenze unterschritten", 198,
                     power_limit_condition=BatPowerLimitCondition.PRICE_LIMIT,
                     price_limit_activated=True,
                     price_limit=0.30,
                     power_limit_mode=BatPowerLimitMode.MODE_CHARGE_PV_PRODUCTION),
    BatControlParams("Preisgrenze, Entladung sperren, Grenze greift nicht", None,
                     power_limit_condition=BatPowerLimitCondition.PRICE_LIMIT,
                     price_limit_activated=True,
                     price_limit=0.10,
                     power_limit_mode=BatPowerLimitMode.MODE_NO_DISCHARGE),
    # Aktive Ladung
    BatControlParams("Preisgrenze, Grenze deaktiviert, Eigenregelung", None,
                     power_limit_condition=BatPowerLimitCondition.PRICE_LIMIT,
                     price_charge_activated=False,
                     charge_limit=0.40),
    BatControlParams("Preisgrenze, Grenze unterschritten, Ladung", 5000,
                     power_limit_condition=BatPowerLimitCondition.PRICE_LIMIT,
                     price_charge_activated=True,
                     charge_limit=0.30),
    BatControlParams("Preisgrenze, Grenze greift nicht, Eigenregelung", None,
                     power_limit_condition=BatPowerLimitCondition.PRICE_LIMIT,
                     price_charge_activated=True,
                     charge_limit=0.10),
]


@pytest.mark.parametrize("params", cases, ids=[c.name for c in cases])
def test_control_price_limit(params: BatControlParams, data_, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(data.data.optional_data, "ep_get_current_price", Mock(return_value=0.2))
    b_all = BatAll()
    b_all.data.config.bat_control_activated = params.bat_control_activated
    b_all.data.config.power_limit_mode = params.power_limit_mode
    b_all.data.config.power_limit_condition = params.power_limit_condition
    b_all.data.config.manual_mode = params.bat_manual_mode
    b_all.data.get.power_limit_controllable = params.power_limit_controllable
    b_all.data.config.bat_control_min_soc = params.bat_control_min_soc
    b_all.data.config.bat_control_max_soc = params.bat_control_max_soc
    b_all.data.config.price_limit_activated = params.price_limit_activated
    b_all.data.config.price_charge_activated = params.price_charge_activated
    b_all.data.config.price_limit = params.price_limit
    b_all.data.config.charge_limit = params.charge_limit

    b_all.data.get.power = params.bat_power
    # b_all.data.get.soc = 50.0
    data.data.optional_data.data.electricity_pricing.configured = True
    data.data.counter_all_data = hierarchy_standard()
    data.data.counter_all_data.data.set.home_consumption = 456
    data.data.pv_all_data.data.get.power = -654
    data.data.cp_all_data.data.get.power = 1400
    data.data.counter_data["counter0"].data.get.power = params.evu_power
    data.data.bat_all_data = b_all

    get_evu_counter_mock = Mock(return_value=data.data.counter_data["counter0"])
    monkeypatch.setattr(data.data.counter_all_data, "get_evu_counter", get_evu_counter_mock)
    get_bat_components_by_controllability_mock = Mock(return_value=([MqttBat(MqttBatSetup(id=2), device_id=0)], []))
    data.data.bat_data["bat2"].data.get.soc = params.bat_soc
    data.data.bat_data["bat2"].data.get.max_charge_power = params.max_charge_power
    data.data.bat_data["bat2"].data.get.max_discharge_power = params.max_discharge_power
    monkeypatch.setattr(bat_all, "get_bat_components_by_controllability",
                        get_bat_components_by_controllability_mock)

    data.data.bat_all_data.get_power_limit()
    data.data.bat_all_data._set_bat_power_active_control(data.data.bat_all_data.data.set.power_limit)

    assert data.data.bat_data["bat2"].data.set.power_limit == params.expected_power_limit_bat


@pytest.mark.parametrize(
    "control_activated, condition, limit, manual_mode, expected_result",
    [
        pytest.param(False,
                     BatPowerLimitCondition.MANUAL.value,
                     BatPowerLimitMode.MODE_NO_DISCHARGE.value,
                     ManualMode.MANUAL_DISABLE.value, True,
                     id="Speichersteuerung nicht aktiviert, aber aktiviert -> laden"),
        pytest.param(True,
                     BatPowerLimitCondition.MANUAL.value,
                     BatPowerLimitMode.MODE_NO_DISCHARGE.value,
                     ManualMode.MANUAL_DISABLE.value, True,
                     id="Manuell, Eigenregelung, volle Entladesperre -> nicht laden"),
        pytest.param(True,
                     BatPowerLimitCondition.MANUAL.value,
                     BatPowerLimitMode.MODE_DISCHARGE_HOME_CONSUMPTION.value,
                     ManualMode.MANUAL_LIMIT.value, False,
                     id="Manuell, Entladung in Fahrzeuge sperren -> nicht laden"),
        pytest.param(True,
                     BatPowerLimitCondition.MANUAL.value,
                     BatPowerLimitMode.MODE_CHARGE_PV_PRODUCTION.value,
                     ManualMode.MANUAL_CHARGE.value, False,
                     id="Manuell, PV-Ertrag speichern -> nicht laden"),
        pytest.param(True,
                     BatPowerLimitCondition.VEHICLE_CHARGING.value,
                     BatPowerLimitMode.MODE_NO_DISCHARGE.value,
                     ManualMode.MANUAL_DISABLE.value, False,
                     id="Fahrzeuge laden, volle Entladesperre -> nicht laden"),
        pytest.param(True,
                     BatPowerLimitCondition.VEHICLE_CHARGING.value,
                     BatPowerLimitMode.MODE_DISCHARGE_HOME_CONSUMPTION.value,
                     ManualMode.MANUAL_DISABLE.value, False,
                     id="Fahrzeuge laden, Entladung in Fahrzeuge sperren -> nicht laden"),
        pytest.param(True,
                     BatPowerLimitCondition.VEHICLE_CHARGING.value,
                     BatPowerLimitMode.MODE_CHARGE_PV_PRODUCTION.value,
                     ManualMode.MANUAL_DISABLE.value, False,
                     id="Fahrzeuge laden, PV-Ertrag speichern -> nicht laden"),
        pytest.param(True,
                     BatPowerLimitCondition.PRICE_LIMIT.value,
                     BatPowerLimitMode.MODE_NO_DISCHARGE.value,
                     ManualMode.MANUAL_DISABLE.value, False,
                     id="Preislimit, volle Entladesperre -> nicht laden"),
        pytest.param(True,
                     BatPowerLimitCondition.PRICE_LIMIT.value,
                     BatPowerLimitMode.MODE_DISCHARGE_HOME_CONSUMPTION.value,
                     ManualMode.MANUAL_DISABLE.value, False,
                     id="Preislimit, Entladung in Fahrzeuge sperren -> nicht laden"),

    ]
)
def test_time_charging_min_bat_soc_allowed(control_activated: bool,
                                           condition: BatPowerLimitCondition,
                                           limit: BatPowerLimitMode,
                                           manual_mode: ManualMode,
                                           expected_result: bool):
    # setup
    b = BatAll()
    b.data.config.configured = True
    b.data.config.power_limit_condition = condition
    b.data.config.power_limit_mode = limit
    b.data.config.bat_control_activated = control_activated
    b.data.config.manual_mode = manual_mode

    # execution
    result = b.time_charging_min_bat_soc_allowed()

    # evaluation
    assert result == expected_result


@pytest.mark.parametrize(
    "ep_configured, price_limit_activated, price_charge_activated, price_threshold_mock, expected_result",
    [
        pytest.param(False, True, True, [True, True], True,
                     id="Preislimit aktiviert, aber kein Preis konfiguriert -> Eigenregelung -> laden"),
        pytest.param(True, True, False, [True], True,
                     id="Strompreis für Regelmodus, Preis unter Limit -> laden"),
        pytest.param(True, True, False, [False], False,
                     id="Strompreis für Regelmodus, Preis über Limit -> nicht laden"),
        pytest.param(True, False, True, [True], True,
                     id="Strompreis für aktives Laden, Preis unter Limit -> laden"),
        pytest.param(True, False, True, [False], False,
                     id="Strompreis für aktives Laden, Preis unter Limit -> nicht laden"),
        pytest.param(True, False, False, [], False,
                     id="beide Strompreise deaktiviert -> nicht laden"),
    ]
)
def test_time_charging_min_bat_soc_allowed_pricing(ep_configured: bool,
                                                   price_limit_activated: bool,
                                                   price_charge_activated: bool,
                                                   price_threshold_mock: List[bool],
                                                   expected_result: bool,
                                                   monkeypatch: pytest.MonkeyPatch):
    # setup
    b = BatAll()
    b.data.config.configured = True
    b.data.config.power_limit_condition = BatPowerLimitCondition.PRICE_LIMIT
    b.data.config.power_limit_mode = BatPowerLimitMode.MODE_CHARGE_PV_PRODUCTION
    b.data.config.price_limit_activated = price_limit_activated
    b.data.config.price_charge_activated = price_charge_activated
    data.data.optional_data.data.electricity_pricing.configured = ep_configured
    b.data.config.bat_control_activated = True

    monkeypatch.setattr(data.data.optional_data, "ep_is_charging_allowed_price_threshold",
                        Mock(side_effect=price_threshold_mock))

    # execution
    result = b.time_charging_min_bat_soc_allowed()

    # evaluation
    assert result == expected_result
