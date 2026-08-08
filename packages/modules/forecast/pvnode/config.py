from dataclasses import dataclass, field


@dataclass
class PvNodeConfiguration:
    api_key: str = ""
    plant_id: str = ""
    peak_power_kw: float = 0.0
    system_loss: float = 0.0


@dataclass
class PvNode:
    name: str = "PVNode V2"
    type: str = "pvnode"
    official: bool = True
    configuration: PvNodeConfiguration = field(default_factory=PvNodeConfiguration)
