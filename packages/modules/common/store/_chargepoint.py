from modules.common.component_state import ChargepointState
from modules.common.store import ValueStore
from modules.common.store._api import LoggingValueStore
from modules.common.store._broker import pub_to_broker
from modules.common.store.ramdisk import files
from helpermodules import compatibility


class ChargepointValueStoreRamdisk(ValueStore[ChargepointState]):
    def __init__(self, cp_id: int):
        self.num = cp_id

    def set(self, cp_state: ChargepointState):
        charge_point = files.charge_points[self.num]
        charge_point.is_charging.write(cp_state.charge_state)
        charge_point.voltages.write(cp_state.voltages)
        charge_point.currents.write(cp_state.currents)
        charge_point.energy.write(cp_state.imported)
        charge_point.is_plugged.write(cp_state.plug_state)
        charge_point.power.write(cp_state.power)


class ChargepointValueStoreBroker(ValueStore[ChargepointState]):
    def __init__(self, cp_id: int):
        self.num = cp_id

    def set(self, state: ChargepointState) -> None:
        self.state = state

    def update(self):
        pub_to_broker("openWB/set/chargepoint/" + str(self.num) + "/get/voltages", self.state.voltages, 2)
        pub_to_broker("openWB/set/chargepoint/" + str(self.num) + "/get/currents", self.state.currents, 2)
        pub_to_broker("openWB/set/chargepoint/" + str(self.num) + "/get/power_factors", self.state.power_factors, 2)
        pub_to_broker("openWB/set/chargepoint/" + str(self.num) + "/get/imported", self.state.imported, 2)
        pub_to_broker("openWB/set/chargepoint/" + str(self.num) + "/get/exported", self.state.exported, 2)
        pub_to_broker("openWB/set/chargepoint/" + str(self.num) + "/get/power", self.state.power, 2)
        pub_to_broker("openWB/set/chargepoint/" + str(self.num) + "/get/phases_in_use", self.state.phases_in_use, 2)
        pub_to_broker("openWB/set/chargepoint/" + str(self.num) + "/get/charge_state", self.state.charge_state, 2)
        pub_to_broker("openWB/set/chargepoint/" + str(self.num) + "/get/plug_state", self.state.plug_state, 2)
        pub_to_broker("openWB/set/chargepoint/" + str(self.num) + "/get/rfid", self.state.rfid)


def get_chargepoint_value_store(id: int) -> ValueStore[ChargepointState]:
    return LoggingValueStore(
        ChargepointValueStoreRamdisk(id) if compatibility.is_ramdisk_in_use() else ChargepointValueStoreBroker(id)
    )
