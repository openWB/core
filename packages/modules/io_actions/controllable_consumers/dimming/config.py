from dataclasses import dataclass, field
from typing import Dict, List, Optional
from dataclass_utils.factories import empty_io_pattern_factory, empty_list_factory
from modules.io_actions.groups import ActionGroup


@dataclass
class DimmingConfig:
    io_device: Optional[int] = None
    input_pattern: List[Dict] = field(default_factory=empty_io_pattern_factory)
    devices: List[Dict[str]] = field(default_factory=empty_list_factory)
    # [{"type": "cp", "id": 0},
    # {"type": "io", "id": 1, "digital_output": "SofortLa"}]
    max_import_power: int = 0
    fixed_import_power: float = 0  # don't show in UI


class DimmingSetup:
    def __init__(self,
                 name: str = "Dimmen per HEMS",
                 type: str = "dimming",
                 id: int = 0,
                 configuration: DimmingConfig = None):
        self.name = name
        self.id = id
        self.configuration = configuration or DimmingConfig()
        self.type = type
        self.group = ActionGroup.CONTROLLABLE_CONSUMERS.value
