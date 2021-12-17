from helpermodules import compatibility
from modules.common.component_state import CarState
from modules.common.store import ValueStore
from modules.common.store._broker import pub_to_broker
from modules.common.store._ramdisk import ramdisk_write


class CarValueStoreRamdisk(ValueStore[CarState]):
    def __init__(self, charge_point: int):
        self.filename = "soc" if charge_point == 1 else "soc1"

    def set(self, state: CarState) -> None:
        ramdisk_write(self.filename, state.soc, 0)


class CarValueStoreBroker(ValueStore[CarState]):
    def __init__(self, vehicle_id: int):
        self.vehicle_id = vehicle_id

    def set(self, state: CarState) -> None:
        pub_to_broker("openWB/set/vehicle/"+str(self.vehicle_id)+"/get/soc", state.soc)
        pub_to_broker("openWB/set/vehicle/"+str(self.vehicle_id)+"/get/timestamp_last_request", state.timestamp)


def get_car_value_store(id: int) -> ValueStore[CarState]:
    if compatibility.is_ramdisk_in_use():
        return CarValueStoreRamdisk(id)
    return CarValueStoreBroker(id)
