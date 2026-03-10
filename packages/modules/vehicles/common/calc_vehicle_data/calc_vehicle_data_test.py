from modules.common.abstract_vehicle import VehicleUpdateData
from modules.vehicles.common.calc_vehicle_data.calc_vehicle_data import calc_vehicle_data


def test_calc_vehicle_data():
    # setup & execution
    soc, range = calc_vehicle_data(VehicleUpdateData(imported=10000, last_soc=12.6,
                                                     efficiency=90,
                                                     battery_capacity=100000,
                                                     average_consump=18),
                                   last_imported=0)

    # evaluation
    assert soc == 21.6
