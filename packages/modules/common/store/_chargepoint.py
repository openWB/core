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
        pub_to_broker("openWB/set/chargepoint/" + str(self.num) +
                      "/get/charging_current", self.state.charging_current, 2)
        pub_to_broker("openWB/set/chargepoint/" + str(self.num) + "/get/charging_power", self.state.charging_power, 2)
        pub_to_broker("openWB/set/chargepoint/" + str(self.num) +
                      "/get/charging_voltage", self.state.charging_voltage, 2)
        pub_to_broker("openWB/set/chargepoint/" + str(self.num) + "/get/voltages", self.state.voltages, 2)
        pub_to_broker("openWB/set/chargepoint/" + str(self.num) + "/get/currents", self.state.currents, 2)
        pub_to_broker("openWB/set/chargepoint/" + str(self.num) + "/get/power_factors", self.state.power_factors, 2)
        if self.state.imported is not None:
            pub_to_broker("openWB/set/chargepoint/" + str(self.num) + "/get/imported", self.state.imported, 2)
        if self.state.exported is not None:
            pub_to_broker("openWB/set/chargepoint/" + str(self.num) + "/get/exported", self.state.exported, 2)
        pub_to_broker("openWB/set/chargepoint/" + str(self.num) + "/get/power", self.state.power, 2)
        pub_to_broker("openWB/set/chargepoint/" + str(self.num) + "/get/powers", self.state.powers, 2)
        pub_to_broker("openWB/set/chargepoint/" + str(self.num) + "/get/frequency", self.state.frequency, 2)
        if self.state.phases_in_use:
            pub_to_broker("openWB/set/chargepoint/" + str(self.num) + "/get/phases_in_use", self.state.phases_in_use, 2)
        pub_to_broker("openWB/set/chargepoint/" + str(self.num) + "/get/charge_state", self.state.charge_state, 2)
        if self.state.plug_state is not None:
            pub_to_broker("openWB/set/chargepoint/" + str(self.num) + "/get/plug_state", self.state.plug_state, 2)
        if self.state.rfid is not None:
            pub_to_broker("openWB/set/chargepoint/" + str(self.num) + "/get/rfid", self.state.rfid)
        if self.state.rfid_timestamp is not None:
            pub_to_broker("openWB/set/chargepoint/" + str(self.num) + "/get/rfid_timestamp", self.state.rfid_timestamp)
        pub_to_broker("openWB/set/chargepoint/" + str(self.num) + "/get/serial_number", self.state.serial_number)
        pub_to_broker("openWB/set/chargepoint/" + str(self.num) + "/get/soc", self.state.soc)
        pub_to_broker("openWB/set/chargepoint/" + str(self.num) + "/get/soc_timestamp", self.state.soc_timestamp)
        pub_to_broker("openWB/set/chargepoint/" + str(self.num) + "/get/evse_current", self.state.evse_current)
        pub_to_broker("openWB/set/chargepoint/" + str(self.num) + "/get/vehicle_id", self.state.vehicle_id)
        pub_to_broker("openWB/set/chargepoint/" + str(self.num) + "/get/max_evse_current", self.state.max_evse_current)
        pub_to_broker("openWB/set/chargepoint/" + str(self.num) + "/get/max_charge_power", self.state.max_charge_power)
        pub_to_broker("openWB/set/chargepoint/" + str(self.num) + "/get/max_discharge_power",
                      self.state.max_discharge_power)
        pub_to_broker("openWB/set/chargepoint/" + str(self.num) + "/get/version", self.state.version)
        pub_to_broker("openWB/set/chargepoint/" + str(self.num) + "/get/current_branch", self.state.current_branch)
        pub_to_broker("openWB/set/chargepoint/" + str(self.num) + "/get/current_commit", self.state.current_commit)
        pub_to_broker("openWB/set/chargepoint/" + str(self.num) + "/get/evse_signaling", self.state.evse_signaling)


def get_chargepoint_value_store(id: int) -> ValueStore[ChargepointState]:
    return LoggingValueStore(ChargepointValueStoreBroker(id))
