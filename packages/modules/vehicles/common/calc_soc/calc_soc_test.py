from modules.common.abstract_vehicle import VehicleUpdateData
from modules.vehicles.common.calc_soc.calc_soc import calc_soc


def test_calc_soc():
    # setup & execution
    soc = calc_soc(VehicleUpdateData(imported=10000, last_soc=12.6),
                   efficiency=90, last_imported=0, battery_capacity=100000)

    # evaluation
    assert soc == 21.6
