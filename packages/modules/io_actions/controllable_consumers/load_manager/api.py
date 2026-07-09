import logging
from typing import Optional, Tuple
from control import data
from control.limiting_value import LimitingValue, LoadmanagementLimit
from modules.common.abstract_io import AbstractIoAction
from modules.common.utils.component_parser import get_io_name_by_id
from modules.io_actions.common import check_fault_state_io_device
from modules.io_actions.controllable_consumers.load_manager.config import LoadManagerSetup
from modules.io_devices.load_manager.config import AnalogInputMapping

from modules.common.abstract_device import DeviceDescriptor

log = logging.getLogger(__name__)
control_command_log = logging.getLogger("steuve_control_command")


class DimmingLoadManager(AbstractIoAction):
    def __init__(self, config: LoadManagerSetup):
        self.config = config
        self.import_power_left = None
        control_command_log.info("Begrenzung per Lastmanager.")
        super().__init__()

    def setup(self) -> None:
        if check_fault_state_io_device(self.config.configuration.io_device):
            max_power = self.config.configuration.max_power_on_failure
        else:
            max_power = data.data.io_states[f"io_states{self.config.configuration.io_device}"
                                            ].data.get.analog_input[AnalogInputMapping.MAX_POWER.name]
        self.import_power_left = max_power

    def loadmanager_get_import_power_left(self) -> Tuple[Optional[float], LoadmanagementLimit]:
        if check_fault_state_io_device(self.config.configuration.io_device):
            return (self.import_power_left, LoadmanagementLimit(
                LimitingValue.CONTROLLABLE_CONSUMERS_ERROR.value.format(get_io_name_by_id(
                    self.config.configuration.io_device)),
                LimitingValue.CONTROLLABLE_CONSUMERS_ERROR))
        return self.import_power_left, LoadmanagementLimit(LimitingValue.DIMMING.value, LimitingValue.DIMMING)


def create_action(config: LoadManagerSetup, parent_device_type: str):
    return DimmingLoadManager(config=config)


device_descriptor = DeviceDescriptor(configuration_factory=LoadManagerSetup)
