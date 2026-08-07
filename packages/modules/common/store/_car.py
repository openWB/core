from modules.common.component_state import CarState
from modules.common.store import ValueStore
from modules.common.store._api import LoggingValueStore
from modules.common.store._broker import pub_to_broker


class CarValueStoreBroker(ValueStore[CarState]):
    def __init__(self, vehicle_id: int):
        self.vehicle_id = vehicle_id

    def set(self, state: CarState) -> None:
        self.state = state

    def update(self):
        pub_to_broker("openWB/set/vehicle/"+str(self.vehicle_id)+"/get/soc", self.state.soc, 2)
        pub_to_broker("openWB/set/vehicle/"+str(self.vehicle_id)+"/get/range", self.state.range, 2)
        pub_to_broker("openWB/set/vehicle/"+str(self.vehicle_id)+"/get/soc_timestamp", self.state.soc_timestamp)
        pub_to_broker("openWB/set/vehicle/"+str(self.vehicle_id)+"/get/odometer", self.state.odometer, 2)


def get_car_value_store(id: int) -> ValueStore[CarState]:
    return LoggingValueStore(CarValueStoreBroker(id))
