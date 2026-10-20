from dataclasses import dataclass, field
from typing import Optional


@dataclass
class PvNodeConfiguration:
    api_key: Optional[str] = None
    plant_id: Optional[str] = None


@dataclass
class PvNode:
    name: str = "PVNode V2"
    type: str = "pvnode"
    official: bool = False
    configuration: PvNodeConfiguration = field(default_factory=PvNodeConfiguration)
