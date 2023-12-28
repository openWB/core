from modules.common.component_state import RcrState
from modules.common.store import ValueStore
from modules.common.store._api import LoggingValueStore
from modules.common.store._broker import pub_to_broker


class RippleControlReceiverValueStore(ValueStore[RcrState]):
    def __init__(self):
        pass

    def set(self, state: RcrState) -> None:
        self.state = state

    def update(self):
        pub_to_broker("openWB/set/general/ripple_control_receiver/get/r1_blocking", self.state.r1_blocking)
        pub_to_broker("openWB/set/general/ripple_control_receiver/get/r2_blocking", self.state.r2_blocking)


def get_ripple_control_receiver_value_store() -> ValueStore[RcrState]:
    return LoggingValueStore(RippleControlReceiverValueStore())
