from dataclasses import dataclass, field
from typing import Dict, Union
from modules.io_actions.dimming.api import Dimming
from modules.io_actions.dimming_direct_control.api import DimmingDirectControl
from modules.io_actions.ripple_control_receiver.api import RippleControlReceiver


@dataclass
class Get:
    analog_input: Dict[int, float] = None
    digital_input: Dict[int, bool] = None
    analog_output: Dict[int, float] = None
    digital_output: Dict[int, bool] = None


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

    def dimming_get_import_power_left(self, cp_num: int) -> float:
        for action in self.actions.values():
            if isinstance(action, Dimming):
                if cp_num in action.config.config.cp_ids:
                    return action.dimming_get_import_power_left(cp_num)

    def dimming_set_import_power_left(self, cp_num: int, used_power: float) -> float:
        for action in self.actions.values():
            if isinstance(action, Dimming):
                if cp_num in action.config.config.cp_ids:
                    return action.dimming_set_import_power_left(cp_num, used_power)

    def dimming_via_direct_control(self, cp_num: int) -> float:
        for action in self.actions.values():
            if isinstance(action, DimmingDirectControl):
                if cp_num == action.config.config.cp_id:
                    return action.dimming_via_direct_control(cp_num)

    def ripple_control_receiver(self, cp_num: int) -> float:
        for action in self.actions.values():
            if isinstance(action, RippleControlReceiver):
                if cp_num in action.config.config.cp_ids:
                    return action.ripple_control_receiver(cp_num)
