from control import data
from modules.common.abstract_device import DeviceDescriptor
from modules.io_actions.controllable_consumers.ripple_control_receiver.config import RippleControlReceiverSetup


class RippleControlReceiver:
    def __init__(self, config: RippleControlReceiverSetup):
        self.config = config

    def ripple_control_receiver(self, cp_num: int) -> None:
        if cp_num in self.config.config.cp_ids:
            if data.data.io_states[f"io_states{self.config.config.io_device}"].data.get.digital_input[
                    self.config.config.digital_input] == self.config.config.blocking_state:
                return True
            else:
                return False
        else:
            return False


def create_action(config: RippleControlReceiverSetup):
    return RippleControlReceiver(config=config)


device_descriptor = DeviceDescriptor(configuration_factory=RippleControlReceiverSetup)
