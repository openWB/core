from dataclasses import dataclass, field
from typing import Dict, Optional, Union
from control import data
from helpermodules.constants import NO_ERROR
from modules.io_actions.controllable_consumers.dimming.api import Dimming
from modules.io_actions.controllable_consumers.dimming_direct_control.api import DimmingDirectControl
from modules.io_actions.controllable_consumers.ripple_control_receiver.api import RippleControlReceiver


@dataclass
class Get:
    analog_input: Dict[int, float] = None
    digital_input: Dict[int, bool] = None
    analog_output: Dict[int, float] = None
    digital_output: Dict[int, bool] = None
    fault_str: str = NO_ERROR
    fault_state: int = 0


def get_factory():
    return Get()


@dataclass
class IoDeviceData:
    get: Get = field(default_factory=get_factory)


class IoStates:
    def __init__(self, num: int):
        self.num = num
        self.data = IoDeviceData()


class IoActions:
    def __init__(self):
        self.actions: Dict[int, Union[Dimming, DimmingDirectControl, RippleControlReceiver]] = {}

    def setup(self):
        for action in self.actions.values():
            if isinstance(action, Dimming):
                action.setup()

    def dimming_get_import_power_left(self, cp_num: int) -> Optional[float]:
        for action in self.actions.values():
            if isinstance(action, Dimming):
                if data.data.io_states[f"io_states{self.config.configuration.io_device}"].data.get.fault_state == 2:
                    return 0
                if cp_num in action.config.configuration.cp_ids:
                    return action.dimming_get_import_power_left(cp_num)
        else:
            return None

    def dimming_set_import_power_left(self, cp_num: int, used_power: float) -> Optional[float]:
        for action in self.actions.values():
            if isinstance(action, Dimming):
                if cp_num in action.config.configuration.cp_ids:
                    return action.dimming_set_import_power_left(cp_num, used_power)

    def dimming_via_direct_control(self, cp_num: int) -> float:
        for action in self.actions.values():
            if isinstance(action, DimmingDirectControl):
                if data.data.io_states[f"io_states{self.config.configuration.io_device}"].data.get.fault_state == 2:
                    return 0
                if cp_num == action.config.configuration.cp_id:
                    return action.dimming_via_direct_control(cp_num)
        else:
            return None

    def ripple_control_receiver(self, cp_num: int) -> float:
        for action in self.actions.values():
            if data.data.io_states[f"io_states{self.config.configuration.io_device}"].data.get.fault_state == 2:
                return 0
            if isinstance(action, RippleControlReceiver):
                if cp_num in action.config.configuration.cp_ids:
                    return action.ripple_control_receiver(cp_num)
        else:
            return 1
