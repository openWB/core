
from modules.common.abstract_vehicle import VehicleUpdateData
from modules.common.component_state import CarState
from modules.vehicles.common.calc_vehicle_data.calc_vehicle_data import calc_vehicle_data


def test_calc_vehicle_data():
    # setup & execution
    carState = calc_vehicle_data(VehicleUpdateData(imported=10000, last_soc=12.6,
                                                   efficiency=90,
                                                   battery_capacity=100000,
                                                   average_consump=18000),
                                 last_imported=0)

    # evaluation
    # print(f"soc={carState.soc}, range={carState.range}")
    assert isinstance(carState, CarState)
    assert carState.soc == 21.6
    assert carState.range == 120
