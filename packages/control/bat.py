from dataclasses import dataclass, field
import logging

log = logging.getLogger(__name__)


@dataclass
class Get:
    soc: float = 0
    daily_exported: float = 0
    daily_imported: float = 0
    imported: float = 0
    exported: float = 0
    fault_state: int = 0
    fault_str: str = ""
    power: float = 0


def get_factory() -> Get:
    return Get()


@dataclass
class BatData:
    get: Get = field(default_factory=get_factory)


class Bat:

    def __init__(self, index):
        self.data = BatData()
        self.num = index
