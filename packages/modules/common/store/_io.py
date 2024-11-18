from modules.common.component_state import IoState
from modules.common.fault_state import FaultState
from modules.common.store import ValueStore
from modules.common.store._api import LoggingValueStore
from modules.common.store._broker import pub_to_broker


class IoValueStoreBroker(ValueStore[IoState]):
    def __init__(self, num: int) -> None:
        self.num = num

    def set(self, state: IoState) -> None:
        self.state = state

    def update(self):
        try:
            if self.state.digital_input:
                pub_to_broker(f"openWB/set/io/states/{self.num}/get/digital_input", self.state.digital_input)
            if self.state.analog_input:
                pub_to_broker(f"openWB/set/io/states/{self.num}/get/analog_input", self.state.analog_input)
            if self.state.digital_output:
                pub_to_broker(f"openWB/set/io/states/{self.num}/set/digital_output", self.state.digital_output)
            if self.state.analog_output:
                pub_to_broker(f"openWB/set/io/states/{self.num}/set/analog_output", self.state.analog_output)
        except Exception as e:
            raise FaultState.from_exception(e)


def get_io_value_store(num: int) -> ValueStore[IoState]:
    return LoggingValueStore(IoValueStoreBroker(num))
