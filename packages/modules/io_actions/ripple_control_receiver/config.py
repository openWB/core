from dataclasses import dataclass, field
from typing import List
from dataclass_utils.factories import empty_list_factory
from modules.io_actions.groups import ActionGroup


@dataclass
class RippleControlReceiverConfig:
    io_device: int = 0
    digital_input: str = "0"
    cp_ids: List[int] = field(default_factory=empty_list_factory)


class RippleControlReceiverSetup:
    def __init__(self,
                 name: str = "RSE-Kontakt",
                 type: str = "ripple_control_receiver",
                 id: int = 0,
                 config: RippleControlReceiverConfig = None):
        self.name = name
        self.id = id
        self.config = config or RippleControlReceiverConfig()
        self.type = type
        self.group = ActionGroup.CONTROLLABLE_CONSUMERS_ACTIONS.value
