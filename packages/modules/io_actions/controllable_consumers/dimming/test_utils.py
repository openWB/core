import pytest
from unittest.mock import Mock

from control import data
from .utils import calc_dimming_surplus


@pytest.fixture()
def mock_data() -> None:
    data.data_init(Mock())


@pytest.mark.parametrize(
    "pv_power,bat_power,expected",
    [
        pytest.param(-1000, 0, 1000, id="nur PV-Überschuss"),
        pytest.param(200, 0, 0, id="WR gibt Eigenverbrauch aus"),
        pytest.param(-500, -300, 800, id="PV & Speicher-Entladung"),
        pytest.param(-500, 400, 500, id="Speicher wird geladen"),
        pytest.param(-500, 0, 500, id="Speicher gesperrt"),
    ]
)
def test_calc_dimming_surplus(mock_data, pv_power, bat_power, expected):
    data.data.pv_all_data.data.get.power = pv_power
    data.data.bat_all_data.data.get.power = bat_power
    assert calc_dimming_surplus() == expected
