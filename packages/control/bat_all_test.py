from dataclasses import dataclass
from typing import Optional
from unittest.mock import Mock
import pytest

from control.bat_all import BatAll
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
    switch_on_soc_reached: bool
    expected_charging_power_left: float
    expected_msg: Optional[str]
    expected_switch_on_soc_reached: bool


cases = [
    Params("Laderegelung nicht freigegeben, Einschalt-SoC konfiguriert", PvCharging(bat_prio=False,
           charging_power_reserve=0), 61, False, 500, f'Laderegelung wurde {BatAll.REACH_SWITCH_ON_SOC[0]}', True),
    Params("Laderegelung nicht freigegeben, Einschalt-SoC konfiguriert", PvCharging(bat_prio=False,
           charging_power_reserve=0), 60, False, 0, f'Laderegelung wurde {BatAll.REACH_SWITCH_ON_SOC[1]}', False),
    Params("Laderegelung nicht freigegeben, nur Ausschalt-SoC konfiguriert",
           PvCharging(bat_prio=False, charging_power_reserve=0, switch_on_soc=0),
           41, False, 500, f'Laderegelung wurde {BatAll.REACH_SWITCH_OFF_SOC[0]}', True),
    Params("Laderegelung nicht freigegeben, nur Ausschalt-SoC konfiguriert",
           PvCharging(bat_prio=False, charging_power_reserve=0, switch_on_soc=0),
           40, False, 0, f'Laderegelung wurde {BatAll.REACH_SWITCH_OFF_SOC[1]}', False),
    Params("Laderegelung nicht freigegeben, kein Ein&Ausschalt-SoC konfiguriert", PvCharging(bat_prio=False,
           charging_power_reserve=0, switch_on_soc=0, switch_off_soc=0), 40, False, 500, None, False),
    Params("Laderegelung freigegeben, ", PvCharging(bat_prio=False, charging_power_reserve=0),
           41, True, 500, f'Laderegelung wurde {BatAll.REACH_SWITCH_OFF_SOC[0]}', True),
    Params("Laderegelung freigegeben, ", PvCharging(bat_prio=False, charging_power_reserve=0),
           40, True, 0, f'Laderegelung wurde {BatAll.REACH_SWITCH_OFF_SOC[1]}', False),
    Params("Laderegelung freigegeben, kein Ausschalt-Soc konfiguriert",
           PvCharging(bat_prio=False, charging_power_reserve=0, switch_off_soc=0),
           41, True, 500, f'Laderegelung wurde {BatAll.REACH_ONLY_SWITCH_ON_SOC[0]}', True),
    Params("Laderegelung freigegeben, kein Ausschalt-Soc konfiguriert",
           PvCharging(bat_prio=False, charging_power_reserve=0, switch_off_soc=0),
           0, True, 0, f'Laderegelung wurde {BatAll.REACH_ONLY_SWITCH_ON_SOC[1]}', False),
    Params("Laderegelung nicht freigegeben, Einschalt-SoC konfiguriert, Ladeleistungsreserve",
           PvCharging(bat_prio=False),
           61, False, 300, f'Laderegelung wurde {BatAll.REACH_SWITCH_ON_SOC[0]}', True),
    Params("EV-Vorrang", PvCharging(bat_prio=True), 51, False, 1000,
           "Erlaubte Entlade-Leistung nutzen (1000W, davon bisher ungeutzt 1000W)", False),
    Params("EV-Vorrang", PvCharging(bat_prio=True), 50, False, -50, None, False),
]


@pytest.mark.parametrize("params", cases, ids=[c.name for c in cases])
def test_get_charging_power_left(params: Params, caplog, data_fixture):
    # setup
    b = BatAll()
    b.data.set.switch_on_soc_reached = params.switch_on_soc_reached
    b.data.get.power = 500
    b.data.get.soc = params.soc
    data.data.general_data.data.chargemode_config.pv_charging = params.config

    # execution
    b._get_charging_power_left()

    # evaluation
    assert b.data.set.charging_power_left == params.expected_charging_power_left
    assert params.expected_msg is None or params.expected_msg in caplog.text
    assert b.data.set.switch_on_soc_reached == params.expected_switch_on_soc_reached
