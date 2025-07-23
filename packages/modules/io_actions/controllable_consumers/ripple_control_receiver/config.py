from dataclasses import dataclass, field
from typing import Dict, List, Optional
from dataclass_utils.factories import empty_list_factory
from modules.io_actions.groups import ActionGroup


@dataclass
class RippleControlReceiverConfig:
    io_device: Optional[int] = None
    input_pattern: List[Dict] = field(default_factory=empty_list_factory)
    # [{"value": 0.5, "matrix": {"SofortLa": False, "PV": True}}]
    devices: List[Dict] = field(default_factory=empty_list_factory)
    # [{"type": "cp", "id": 0},
    # {"type": "io", "id": 1, "digital_output": "SofortLa"},


class RippleControlReceiverSetup:
    def __init__(self,
                 name: str = "RSE-Kontakt",
                 type: str = "ripple_control_receiver",
                 id: int = 0,
                 configuration: RippleControlReceiverConfig = None):
        self.name = name
        self.id = id
        self.configuration = configuration or RippleControlReceiverConfig()
        self.type = type
        self.group = ActionGroup.CONTROLLABLE_CONSUMERS.value
