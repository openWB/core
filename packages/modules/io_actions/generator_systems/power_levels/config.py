from dataclasses import dataclass, field
from typing import List, Optional
from dataclass_utils.factories import empty_list_factory
from modules.io_actions.groups import ActionGroup


@dataclass
class PowerLevelsConfig:
    io_device: Optional[int] = None
    digital_input: List[int] = field(default_factory=empty_list_factory)
    component_id: Optional[int] = None


class PowerLevelsSetup:
    def __init__(self,
                 name: str = "Leistungsstufen für Erzeugungsanlagen (EZA)",
                 type: str = "power_levels",
                 id: int = 0,
                 configuration: PowerLevelsConfig = None):
        self.name = name
        self.id = id
        self.configuration = configuration or PowerLevelsConfig()
        self.type = type
        self.group = ActionGroup.GENERATOR_SYSTEMS.value
