#!/usr/bin/python
from dataclasses import dataclass, field
from typing import List, Optional

from dataclass_utils.factories import currents_list_factory, voltages_list_factory
from helpermodules.constants import NO_ERROR


@dataclass
class GlobalHandlerData:
    heartbeat: int = 0
    parent_ip: Optional[str] = None
    configured: bool = False


@dataclass
class InternalChargepointData:
    cp_interruption_duration: int = 0
    parent_cp: Optional[int] = None
    phases_to_use: int = 0
    set_current: float = 0
    trigger_phase_switch: bool = False


def internal_chargepoint_data_factory() -> InternalChargepointData:
    return InternalChargepointData()


@dataclass
class Get:
    charge_state: bool = False
    currents: List[float] = field(default_factory=currents_list_factory)
    evse_current: float = 0
    exported: float = 0
    fault_str: str = NO_ERROR
    fault_state: int = 0
    imported: float = 0
    phases_in_use: int = 0
    plug_state: bool = False
    power: float = 0
    rfid_timestamp: Optional[str] = None
    rfid: Optional[str] = None
    voltages: List[float] = field(default_factory=voltages_list_factory)


def get_factory() -> Get:
    return Get()


@dataclass
class InternalChargepoint:
    data: InternalChargepointData = field(default_factory=internal_chargepoint_data_factory)
    get: Get = field(default_factory=get_factory)


@dataclass
class RfidData:
    last_tag: str = ""
