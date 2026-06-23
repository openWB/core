from dataclasses import dataclass
from typing import List
from unittest.mock import Mock

import pytest

from control import data
from control.chargepoint.chargepoint import Chargepoint
from control.chargepoint.chargepoint_all import AllChargepoints
from helpermodules.constants import NO_ERROR


@dataclass
class Params:
    name: str
    cp_values: List[Chargepoint]
    expected_power: float
    expected_imported: float
    expected_exported: float
    expected_fault_state: int
    expected_fault_str: str


def cp_mock(num: int, imported: float, exported: float, power: float, fault_state: int) -> Mock:
    return Mock(spec=Chargepoint, num=num, data=Mock(get=Mock(imported=imported,
                                                              exported=exported,
                                                              power=power,
                                                              fault_state=fault_state)))


cases = [
    Params(
        name="Alle Ladepunkte fehlerfrei",
        cp_values=[
            cp_mock(1, 1000, 100, 1200, 0),
            cp_mock(2, 2000, 200, 2400, 0),
        ],
        expected_power=3600,
        expected_imported=3000,
        expected_exported=300,
        expected_fault_state=0,
        expected_fault_str=NO_ERROR,
    ),
    Params(
        name="Mindestens ein Ladepunkt mit Fehler",
        cp_values=[
            cp_mock(1, 1000, 100, 1200, 0),
            cp_mock(2, 2000, 200, 2400, 2),
        ],
        expected_power=3600,
        expected_imported=3000,
        expected_exported=300,
        expected_fault_state=2,
        expected_fault_str=(
            "Bitte die Statusmeldungen der Ladepunkte prüfen. "
            "Es haben nicht alle Ladepunkte aktuelle Zählerstände geliefert."
        ),
    ),
]


@pytest.mark.parametrize("params", cases, ids=[c.name for c in cases])
def test_get_cp_sum(params: Params):
    # setup
    data.data_init(Mock())
    data.data.cp_data = {f"cp{index}": cp for index, cp in enumerate(params.cp_values)}
    cp_all = AllChargepoints()

    # execution
    cp_all.get_cp_sum()

    # evaluation
    assert cp_all.data.get.power == params.expected_power
    assert cp_all.data.get.imported == params.expected_imported
    assert cp_all.data.get.exported == params.expected_exported
    assert cp_all.data.get.fault_state == params.expected_fault_state
    assert cp_all.data.get.fault_str == params.expected_fault_str
