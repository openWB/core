from dataclasses import dataclass, field
from typing import Dict, List, Optional
from dataclass_utils.factories import empty_io_pattern_boolean_factory, empty_list_factory
from modules.io_actions.groups import ActionGroup


@dataclass
class LoadManagerConfig:
    io_device: Optional[int] = None
    input_pattern: List[Dict] = field(default_factory=empty_io_pattern_boolean_factory)
    devices: List[Dict] = field(default_factory=empty_list_factory)
    # [{"type": "cp", "id": 0},
    # {"type": "io", "id": 1, "digital_output": "SofortLa"}]
    max_import_power: int = 0
    max_power_on_failure: float = 0
    max_current_on_failure: float = 0


class LoadManagerSetup:
    def __init__(self,
                 name: str = "Begrenzung per Lastmanager",
                 type: str = "load_manager",
                 id: int = 0,
                 configuration: LoadManagerConfig = None):
        self.name = name
        self.id = id
        self.configuration = configuration or LoadManagerConfig()
        self.type = type
        self.group = ActionGroup.CONTROLLABLE_CONSUMERS.value
