from dataclasses import dataclass, field
from typing import Dict, List, Optional
from modules.io_actions.groups import ActionGroup


def default_input_pattern_factory() -> List:
    return [
        {"value": 1, "input_matrix": {}},
        {"value": 0.6, "input_matrix": {}},
        {"value": 0.3, "input_matrix": {}},
        {"value": 0, "input_matrix": {}}
    ]


@dataclass
class PowerLevelsConfig:
    io_device: Optional[int] = None
    # [{"value": 0.5, "input_matrix": {"1": False, "2": True}}]
    input_pattern: List[Dict] = field(default_factory=default_input_pattern_factory)
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
