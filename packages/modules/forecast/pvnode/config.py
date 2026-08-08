from dataclasses import dataclass, field
from typing import Optional


@dataclass
class PvNodeConfiguration:
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    peak_power_kw: Optional[float] = None
    system_loss: Optional[float] = None
    api_key: Optional[str] = None
    plant_id: Optional[str] = None


@dataclass
class PvNode:
    name: str = "PVNode V2"
    type: str = "pvnode"
    official: bool = True
    configuration: PvNodeConfiguration = field(default_factory=PvNodeConfiguration)
