from dataclasses import dataclass, field
from typing import Dict, Optional, Union
from control import data
from control.limiting_value import LimitingValue
from helpermodules.constants import NO_ERROR
from modules.common.utils.component_parser import get_io_name_by_id
from modules.io_actions.controllable_consumers.dimming.api_eebus import DimmingEebus
from modules.io_actions.controllable_consumers.dimming.api_io import DimmingIo
from modules.io_actions.controllable_consumers.dimming_direct_control.api import DimmingDirectControl
from modules.io_actions.controllable_consumers.ripple_control_receiver.api import RippleControlReceiver
from modules.io_actions.generator_systems.stepwise_control.api_eebus import StepwiseControlEebus
from modules.io_actions.generator_systems.stepwise_control.api_io import StepwiseControlIo


@dataclass
class Get:
    analog_input: Dict[int, float] = None
    analog_output: Dict[int, float] = None
    digital_input: Dict[int, bool] = None
    digital_output: Dict[int, bool] = None
    analog_input_prev: Dict[int, float] = None
    analog_output_prev: Dict[int, float] = None
    digital_input_prev: Dict[int, bool] = None
    digital_output_prev: Dict[int, bool] = None
    fault_str: str = NO_ERROR
    fault_state: int = 0


def get_factory():
    return Get()


@dataclass
class Set:
    analog_output: Dict[int, float] = None
    analog_output_prev: Dict[int, float] = None
    digital_output: Dict[int, bool] = None
    digital_output_prev: Dict[int, bool] = None


def set_factory():
    return Set()


@dataclass
class IoDeviceData:
    get: Get = field(default_factory=get_factory)
    set: Set = field(default_factory=set_factory)


class IoStates:
    def __init__(self, num: Union[int, str]):
        self.num = num
        self.data = IoDeviceData()


class IoActions:
    def __init__(self):
        self.actions: Dict[int, Union[DimmingIo, DimmingEebus, DimmingDirectControl,
                                      RippleControlReceiver, StepwiseControlEebus, StepwiseControlIo]] = {}

    def setup(self):
        for action in self.actions.values():
            action.setup()

    def _check_fault_state_io_device(self, io_device: int) -> None:
        if data.data.io_states[f"io_states{io_device}"].data.get.fault_state == 2:
            raise ValueError(LimitingValue.CONTROLLABLE_CONSUMERS_ERROR.value.format(get_io_name_by_id(io_device)))

    def dimming_get_import_power_left(self, device: Dict) -> Optional[float]:
        for action in self.actions.values():
            if isinstance(action, (DimmingIo, DimmingEebus)):
                for d in action.config.configuration.devices:
                    if device == d:
                        self._check_fault_state_io_device(action.config.configuration.io_device)
                        return action.dimming_get_import_power_left()
        else:
            return None

    def dimming_set_import_power_left(self, device: Dict, used_power: float) -> Optional[float]:
        for action in self.actions.values():
            if isinstance(action, (DimmingIo, DimmingEebus)):
                for d in action.config.configuration.devices:
                    if d == device:
                        return action.dimming_set_import_power_left(used_power)

    def dimming_via_direct_control(self, device: Dict) -> Optional[float]:
        for action in self.actions.values():
            if isinstance(action, DimmingDirectControl):
                for d in action.config.configuration.devices:
                    if device == d:
                        self._check_fault_state_io_device(action.config.configuration.io_device)
                        return action.dimming_via_direct_control()
        else:
            return None

    def ripple_control_receiver(self, device: Dict) -> float:
        for action in self.actions.values():
            if isinstance(action, RippleControlReceiver):
                for d in action.config.configuration.devices:
                    if device == d:
                        self._check_fault_state_io_device(action.config.configuration.io_device)
                        return action.ripple_control_receiver()
        else:
            return 1

    def stepwise_control(self, device_id: int) -> Optional[float]:
        for action in self.actions.values():
            if isinstance(action, (StepwiseControlEebus, StepwiseControlIo)):
                if device_id in [component["id"] for component in action.config.configuration.devices]:
                    self._check_fault_state_io_device(action.config.configuration.io_device)
                    return action.control_stepwise()
        else:
            return None
