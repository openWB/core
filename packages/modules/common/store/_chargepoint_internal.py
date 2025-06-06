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
        topic_prefix = f"openWB/set/internal_chargepoint/{self.num}/get"
        pub_to_broker(f"{topic_prefix}/voltages", self.state.voltages, 2)
        pub_to_broker(f"{topic_prefix}/currents", self.state.currents, 2)
        pub_to_broker(f"{topic_prefix}/frequency", self.state.frequency, 2)
        pub_to_broker(f"{topic_prefix}/power_factors", self.state.power_factors, 2)
        pub_to_broker(f"{topic_prefix}/imported", self.state.imported, 2)
        pub_to_broker(f"{topic_prefix}/exported", self.state.exported, 2)
        pub_to_broker(f"{topic_prefix}/power", self.state.power, 2)
        pub_to_broker(f"{topic_prefix}/powers", self.state.powers, 2)
        pub_to_broker(f"{topic_prefix}/phases_in_use", self.state.phases_in_use, 2)
        pub_to_broker(f"{topic_prefix}/charge_state", self.state.charge_state, 2)
        pub_to_broker(f"{topic_prefix}/plug_state", self.state.plug_state, 2)
        pub_to_broker(f"{topic_prefix}/rfid", self.state.rfid)
        pub_to_broker(f"{topic_prefix}/serial_number", self.state.serial_number)
        pub_to_broker(f"{topic_prefix}/evse_current", self.state.evse_current, 2)
        pub_to_broker(f"{topic_prefix}/max_evse_current", self.state.max_evse_current, 2)
        pub_to_broker(f"{topic_prefix}/version", self.state.version)
        pub_to_broker(f"{topic_prefix}/current_branch", self.state.current_branch)
        pub_to_broker(f"{topic_prefix}/current_commit", self.state.current_commit)
        if self.state.soc is not None:
            pub_to_broker(f"{topic_prefix}/get/soc", self.state.soc)
        if self.state.soc_timestamp is not None:
            pub_to_broker(f"{topic_prefix}/soc_timestamp", self.state.soc_timestamp)
        if self.state.rfid_timestamp is not None:
            pub_to_broker(f"{topic_prefix}/vehicle_id", self.state.vehicle_id)


def get_internal_chargepoint_value_store(id: int) -> ValueStore[ChargepointState]:
    return LoggingValueStore(InternalChargepointValueStore(id))
