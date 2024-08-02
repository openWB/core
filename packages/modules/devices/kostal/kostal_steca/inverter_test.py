import pytest
from modules.conftest import SAMPLE_IP

from modules.devices.kostal.kostal_steca.config import KostalStecaInverterSetup
from modules.devices.kostal.kostal_steca.inverter import KostalStecaInverter


@pytest.mark.parametrize("measurements_file, expected_power",
                         [
                             pytest.param("measurements_production.xml", -132.8, id="WR produziert"),
                             pytest.param("measurements_no_production.xml", 0, id="WR produziert nicht"),
                             pytest.param("measurements_no_production_piko3p6mp.xml", 0,
                                          id="WR produziert nicht, Piko 3.6 MP"),
                         ])
def test_get_values(measurements_file, expected_power, requests_mock):
    # setup
    inverter = KostalStecaInverter(KostalStecaInverterSetup(), SAMPLE_IP)

    with open("packages/modules/devices/kostal/kostal_steca/"+measurements_file, "r") as f:
        measurements_sample = f.read()
    requests_mock.get("http://" + SAMPLE_IP + "/measurements.xml", text=measurements_sample)

    with open("packages/modules/devices/kostal/kostal_steca/yields.xml", "r") as f:
        yields_sample = f.read()
    requests_mock.get("http://" + SAMPLE_IP + "/yields.xml", text=yields_sample)

    # execution
    power, exported = inverter.get_values()

    # evaluation
    assert power == expected_power
    assert exported == 12306056
