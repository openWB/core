from modules.common.component_state import ChargepointState
from modules.common.store import ValueStore
from modules.common.store._api import LoggingValueStore
from modules.common.store._broker import pub_to_broker


class InternalChargepointValueStore(ValueStore[ChargepointState]):
    def __init__(self, cp_id: int):
        self.num = cp_id

    def set(self, state: ChargepointState) -> None:
        self.state = state

    def update(self):
        pub_to_broker("openWB/set/internal_chargepoint/" + str(self.num) + "/get/voltages", self.state.voltages, 2)
        pub_to_broker("openWB/set/internal_chargepoint/" + str(self.num) + "/get/currents", self.state.currents, 2)
        pub_to_broker("openWB/set/internal_chargepoint/" + str(self.num) + "/get/frequency", self.state.frequency, 2)
        pub_to_broker("openWB/set/internal_chargepoint/" + str(self.num) +
                      "/get/power_factors", self.state.power_factors, 2)
        pub_to_broker("openWB/set/internal_chargepoint/" + str(self.num) + "/get/imported", self.state.imported, 2)
        pub_to_broker("openWB/set/internal_chargepoint/" + str(self.num) + "/get/exported", self.state.exported, 2)
        pub_to_broker("openWB/set/internal_chargepoint/" + str(self.num) + "/get/power", self.state.power, 2)
        pub_to_broker("openWB/set/internal_chargepoint/" + str(self.num) + "/get/powers", self.state.powers, 2)
        pub_to_broker("openWB/set/internal_chargepoint/" + str(self.num) +
                      "/get/phases_in_use", self.state.phases_in_use, 2)
        pub_to_broker("openWB/set/internal_chargepoint/" + str(self.num) +
                      "/get/charge_state", self.state.charge_state, 2)
        pub_to_broker("openWB/set/internal_chargepoint/" + str(self.num) + "/get/plug_state", self.state.plug_state, 2)
        pub_to_broker("openWB/set/internal_chargepoint/" + str(self.num) + "/get/rfid", self.state.rfid)
        pub_to_broker("openWB/set/internal_chargepoint/" + str(self.num) +
                      "/get/serial_number", self.state.serial_number)
        pub_to_broker("openWB/set/internal_chargepoint/" + str(self.num) +
                      "/get/evse_current", self.state.evse_current, 2)
        pub_to_broker("openWB/set/internal_chargepoint/" + str(self.num) +
                      "/get/max_evse_current", self.state.max_evse_current, 2)


def get_internal_chargepoint_value_store(id: int) -> ValueStore[ChargepointState]:
    return LoggingValueStore(InternalChargepointValueStore(id))
