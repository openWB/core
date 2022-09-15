from modules.common.component_state import ChargepointState
from modules.common.store import ValueStore
from modules.common.store._api import LoggingValueStore
from modules.common.store._broker import pub_to_broker


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
        pub_to_broker("openWB/set/chargepoint/" + str(self.num) + "/get/read_tag", self.state.read_tag)


def get_chargepoint_value_store(id: int) -> ValueStore[ChargepointState]:
    return LoggingValueStore(ChargepointValueStoreBroker(id))
