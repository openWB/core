from control import data
from modules.common.abstract_device import DeviceDescriptor
from modules.io_actions.controllable_consumers.dimming_direct_control.config import DimmingDirectControlSetup


class DimmingDirectControl:
    def __init__(self, config: DimmingDirectControlSetup):
        self.config = config

    def dimming_via_direct_control(self, cp_num: int) -> None:
        if cp_num == self.config.config.cp_id:
            if data.data.io_states[f"io_states{self.config.config.io_device}"].data.get.digital_input[
                    self.config.config.digital_input]:
                return 4200
            else:
                return None
        else:
            return None


def create_action(config: DimmingDirectControlSetup):
    return DimmingDirectControl(config=config)


device_descriptor = DeviceDescriptor(configuration_factory=DimmingDirectControlSetup)
