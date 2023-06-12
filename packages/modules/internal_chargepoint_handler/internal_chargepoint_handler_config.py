#!/usr/bin/python
from dataclasses import dataclass
from typing import Optional


@dataclass
class GlobalHandlerData:
    heartbeat: int = 0
    parent_ip: Optional[str] = None
    configured: bool = False


@dataclass
class InternalChargepointHandlerData:
    cp_interruption_duration: int = 0
    parent_cp: Optional[int] = None
    phases_to_use: int = 0
    set_current: float = 0


@dataclass
class RfidData:
    last_tag: str = ""
