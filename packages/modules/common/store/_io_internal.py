from modules.common.component_state import IoState
from modules.common.store import ValueStore
from modules.common.store._api import LoggingValueStore
from modules.common.store._broker import pub_to_broker


class InternalIoValueStoreBroker(ValueStore[IoState]):
    def __init__(self) -> None:
        pass

    def set(self, state: IoState) -> None:
        self.state = state

    def update(self):
        if self.state.digital_input:
            pub_to_broker("openWB/set/internal_io/states/get/digital_input", self.state.digital_input)
        if self.state.analog_input:
            pub_to_broker("openWB/set/internal_io/states/get/analog_input", self.state.analog_input)
        if self.state.digital_output:
            pub_to_broker("openWB/set/internal_io/states/get/digital_output", self.state.digital_output)
        if self.state.analog_output:
            pub_to_broker("openWB/set/internal_io/states/get/analog_output", self.state.analog_output)


def get_internal_io_value_store() -> ValueStore[IoState]:
    return LoggingValueStore(InternalIoValueStoreBroker())
