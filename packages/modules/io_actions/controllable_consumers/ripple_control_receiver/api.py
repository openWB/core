from control import data
from modules.common.abstract_device import DeviceDescriptor
from modules.io_actions.controllable_consumers.ripple_control_receiver.config import RippleControlReceiverSetup


class RippleControlReceiver:
    def __init__(self, config: RippleControlReceiverSetup):
        self.config = config

    def ripple_control_receiver(self, cp_num: int) -> float:
        if cp_num in self.config.configuration.cp_ids:
            for pattern in self.config.configuration.input_pattern:
                for digital_input, value in pattern["input_matrix"].items():
                    if data.data.io_states[f"io_states{self.config.configuration.io_device}"].data.get.digital_input[
                            digital_input] != value:
                        break
                else:
                    # Alle digitalen Eingänge entsprechen dem Pattern
                    return pattern["value"]
            else:
                # Zustand entpsricht keinem Pattern
                return 0
        else:
            return 1


def create_action(config: RippleControlReceiverSetup):
    return RippleControlReceiver(config=config)


device_descriptor = DeviceDescriptor(configuration_factory=RippleControlReceiverSetup)
