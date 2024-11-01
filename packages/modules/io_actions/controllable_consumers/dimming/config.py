from dataclasses import dataclass, field
from typing import List
from dataclass_utils.factories import empty_list_factory
from modules.io_actions.groups import ActionGroup


@dataclass
class DimmingConfig:
    io_device: int = 0
    digital_input: str = "0"
    cp_ids: List[int] = field(default_factory=empty_list_factory)
    max_import_power: int = 0


class DimmingSetup:
    def __init__(self,
                 name: str = "Dimmen",
                 type: str = "dimming",
                 id: int = 0,
                 configuration: DimmingConfig = None):
        self.name = name
        self.id = id
        self.configuration = configuration or DimmingConfig()
        self.type = type
        self.group = ActionGroup.CONTROLLABLE_CONSUMERS.value
