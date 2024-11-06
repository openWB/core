from dataclasses import dataclass, field
from typing import List
from dataclass_utils.factories import empty_list_factory
from modules.io_actions.groups import ActionGroup


@dataclass
class PowerLevelsConfig:
    io_device: int = 0
    digital_input: List[int] = field(default_factory=empty_list_factory)
    component_id: int = 0


class PowerLevelsSetup:
    def __init__(self,
                 name: str = "Leistungsstufen für Erzeugungsanlagen (EZA)",
                 type: str = "power_level",
                 id: int = 0,
                 configuration: PowerLevelsConfig = None):
        self.name = name
        self.id = id
        self.configuration = configuration or PowerLevelsConfig()
        self.type = type
        self.group = ActionGroup.GENERATOR_SYSTEMS.value
