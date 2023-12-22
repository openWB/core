from modules.common.abstract_vehicle import VehicleUpdateData
from modules.vehicles.common.calc_soc.calc_soc import calc_soc


def test_calc_soc():
    # setup & execution
    soc = calc_soc(VehicleUpdateData(imported=10000), 90, 0, 12.6, 100000)

    # evaluation
    assert soc == 21.6
