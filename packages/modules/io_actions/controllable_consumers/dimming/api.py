import logging
from control import data
from modules.common.abstract_device import DeviceDescriptor
from modules.io_actions.controllable_consumers.dimming.config import DimmingSetup

log = logging.getLogger(__name__)


class Dimming:
    def __init__(self, config: DimmingSetup):
        self.config = config
        self.import_power_left = None

    def setup(self) -> None:
        self.import_power_left = self.config.config.max_import_power + \
            data.data.counter_data[data.data.counter_all_data.get_evu_counter_str()].calc_raw_surplus()
        log.debug(f"Dimmen: {self.import_power_left}W inkl Überschuss")

    def dimming_get_import_power_left(self, cp_num: int) -> None:
        if cp_num in self.config.config.cp_ids:
            if data.data.io_states[f"io_states{self.config.config.io_device}"].data.get.digital_input[
                    self.config.config.digital_input]:
                return self.import_power_left
            else:
                return None
        else:
            return None

    def dimming_set_import_power_left(self, cp_num: int, used_power: float) -> None:
        if cp_num in self.config.config.cp_ids:
            self.import_power_left -= used_power
            log.debug(f"verbleibende Dimm-Leistung: {self.import_power_left}W inkl Überschuss")
            return self.import_power_left
        else:
            return None


def create_action(config: DimmingSetup):
    return Dimming(config=config)


device_descriptor = DeviceDescriptor(configuration_factory=DimmingSetup)
