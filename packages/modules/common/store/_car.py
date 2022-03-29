from helpermodules import compatibility
from helpermodules import timecheck
from modules.common.component_state import CarState
from modules.common.store import ValueStore
from modules.common.store._api import LoggingValueStore
from modules.common.store._broker import pub_to_broker
from modules.common.store.ramdisk import files


class CarValueStoreRamdisk(ValueStore[CarState]):
    def __init__(self, charge_point: int):
        self.file = files.charge_points[charge_point - 1].soc

    def set(self, state: CarState) -> None:
        self.file.write(int(state.soc))


class CarValueStoreBroker(ValueStore[CarState]):
    def __init__(self, vehicle_id: int):
        self.vehicle_id = vehicle_id

    def set(self, state: CarState) -> None:
        pub_to_broker("openWB/set/vehicle/"+str(self.vehicle_id)+"/get/soc", state.soc)
        if state.range:
            pub_to_broker("openWB/set/vehicle/"+str(self.vehicle_id)+"/get/range", state.range)
        pub_to_broker("openWB/set/vehicle/"+str(self.vehicle_id)+"/get/soc_timestamp", timecheck.create_timestamp())


def get_car_value_store(id: int) -> ValueStore[CarState]:
    return LoggingValueStore(
        CarValueStoreRamdisk(id) if compatibility.is_ramdisk_in_use() else CarValueStoreBroker(id)
    )
