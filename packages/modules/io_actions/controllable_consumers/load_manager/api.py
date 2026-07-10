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


class LoadManager(AbstractIoAction):
    def __init__(self, config: LoadManagerSetup):
        self.config = config
        self.import_power_left = None
        self.import_current_left = None
        super().__init__()

    def setup(self) -> None:
        if check_fault_state_io_device(self.config.configuration.io_device):
            log.warning("Fehler des IO-Geräts: Lastmanager aktiviert für Failsafe-Modus.")
            max_power = self.config.configuration.max_power_on_failure
            max_current = self.config.configuration.max_current_on_failure
        else:
            max_power = data.data.io_states[f"io_states{self.config.configuration.io_device}"
                                            ].data.get.analog_input[AnalogInputMapping.MAX_POWER.name]
            max_current = data.data.io_states[f"io_states{self.config.configuration.io_device}"
                                              ].data.get.analog_input[AnalogInputMapping.MAX_CURRENT.name]
        self.import_power_left = max_power
        self.import_current_left = max_current

    def loadmanager_get_import_power_left(self) -> Tuple[Optional[float], LoadmanagementLimit]:
        if check_fault_state_io_device(self.config.configuration.io_device):
            return (self.import_power_left, LoadmanagementLimit(
                LimitingValue.CONTROLLABLE_CONSUMERS_ERROR.value.format(get_io_name_by_id(
                    self.config.configuration.io_device)),
                LimitingValue.CONTROLLABLE_CONSUMERS_ERROR))
        return self.import_power_left, self.import_current_left,  LoadmanagementLimit(LimitingValue.LOADMANAGER.value,
                                                                                      LimitingValue.LOADMANAGER)

    def loadmanager_set_import_power_left(self, used_power: float, used_current: float) -> None:
        if check_fault_state_io_device(self.config.configuration.io_device):
            return (self.import_power_left, LoadmanagementLimit(
                LimitingValue.CONTROLLABLE_CONSUMERS_ERROR.value.format(get_io_name_by_id(
                    self.config.configuration.io_device)),
                LimitingValue.CONTROLLABLE_CONSUMERS_ERROR))
        self.import_power_left -= used_power
        self.import_current_left -= used_current
        log.debug(
            f"verbleibende Dimm-Leistung: {self.import_power_left}W, verbleibender Strom: {self.import_current_left}A")
        return self.import_power_left


def create_action(config: LoadManagerSetup, parent_device_type: str):
    return LoadManager(config=config)


device_descriptor = DeviceDescriptor(configuration_factory=LoadManagerSetup)
