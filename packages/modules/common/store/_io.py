from control import data
from modules.common.component_state import IoState
from modules.common.store import ValueStore
from modules.common.store._api import LoggingValueStore
from modules.common.store._broker import pub_to_broker


class IoValueStoreBroker(ValueStore[IoState]):
    def __init__(self, num: int) -> None:
        self.num = num
        self.state = IoState()

    def set(self, state: IoState) -> None:
        self.state = state

    def update(self):
        if self.state.digital_input:
            pub_to_broker(f"openWB/set/io/states/{self.num}/get/digital_input_prev",
                          data.data.io_states[f"io_states{self.num}"].data.get.digital_input)
            pub_to_broker(f"openWB/set/io/states/{self.num}/get/digital_input", self.state.digital_input)
        if self.state.analog_input:
            pub_to_broker(f"openWB/set/io/states/{self.num}/get/analog_input_prev",
                          data.data.io_states[f"io_states{self.num}"].data.get.analog_input)
            pub_to_broker(f"openWB/set/io/states/{self.num}/get/analog_input", self.state.analog_input)
        if self.state.digital_output:
            pub_to_broker(f"openWB/set/io/states/{self.num}/get/digital_output_prev",
                          data.data.io_states[f"io_states{self.num}"].data.get.digital_output)
            pub_to_broker(f"openWB/set/io/states/{self.num}/get/digital_output", self.state.digital_output)
            pub_to_broker(f"openWB/set/io/states/{self.num}/set/digital_output_prev",
                          data.data.io_states[f"io_states{self.num}"].data.set.digital_output)
            pub_to_broker(f"openWB/set/io/states/{self.num}/set/digital_output", self.state.digital_output)
        if self.state.analog_output:
            pub_to_broker(f"openWB/set/io/states/{self.num}/get/analog_output_prev",
                          data.data.io_states[f"io_states{self.num}"].data.get.analog_output)
            pub_to_broker(f"openWB/set/io/states/{self.num}/get/analog_output", self.state.analog_output)
            pub_to_broker(f"openWB/set/io/states/{self.num}/set/analog_output_prev",
                          data.data.io_states[f"io_states{self.num}"].data.set.analog_output)
            pub_to_broker(f"openWB/set/io/states/{self.num}/set/analog_output", self.state.analog_output)


def get_io_value_store(num: int) -> ValueStore[IoState]:
    return LoggingValueStore(IoValueStoreBroker(num))
