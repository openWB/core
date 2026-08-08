from dataclasses import dataclass, field


@dataclass
class PvNodeConfiguration:
    api_key: str = ""
    plant_id: str = ""


@dataclass
class PvNode:
    name: str = "PVNode V2"
    type: str = "pvnode"
    official: bool = True
    configuration: PvNodeConfiguration = field(default_factory=PvNodeConfiguration)
