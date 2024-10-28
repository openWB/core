from control import data
from modules.common.abstract_device import DeviceDescriptor
from modules.io_actions.dimming.config import DimmingSetup


class Dimming:
    def __init__(self, config: DimmingSetup):
        self.config = config
        # wird jeden zyklus kopiert und daher zurückgesetzt
        self.import_power_left = self.config.config.max_import_power

    def dimming_get_import_power_left(self, cp_num: int) -> None:
        if cp_num in self.config.config.cp_ids:
            if data.data.io_states[self.config.config.io_device].get.digital_input[self.config.config.digital_input]:
                return self.import_power_left
            else:
                return None
        else:
            return None

    def dimming_set_import_power_left(self, cp_num: int, used_power: float) -> None:
        if cp_num in self.config.config.cp_ids:
            self.import_power_left -= used_power
            return self.import_power_left
        else:
            return None


def create_action(config: DimmingSetup):
    return Dimming(config=config)


device_descriptor = DeviceDescriptor(configuration_factory=DimmingSetup)
