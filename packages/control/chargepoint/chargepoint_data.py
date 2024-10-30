from dataclasses import dataclass, field
import threading
from typing import Dict, List, Optional, Protocol
from control.chargepoint.chargepoint_template import CpTemplate

from control.chargepoint.control_parameter import ControlParameter, control_parameter_factory
from control.ev.ev import Ev
from dataclass_utils.factories import currents_list_factory, empty_dict_factory, voltages_list_factory
from helpermodules.constants import NO_ERROR
from modules.common.abstract_chargepoint import AbstractChargepoint


@dataclass
class ConnectedSoc:
    fault_str: str = NO_ERROR
    fault_state: int = 0
    range_charged: float = 0
    range_unit: str = "km"
    range: float = 0
    soc: int = 0
    timestamp: Optional[str] = None


@dataclass
class ConnectedSocConfig:
    configured: str = ""


@dataclass
class ConnectedInfo:
    id: int = 0
    name: str = "Ladepunkt"


@dataclass
class ConnectedConfig:
    average_consumption: float = 17
    charge_template: int = 0
    chargemode: str = "stop"
    current_plan: Optional[int] = 0
    ev_template: int = 0
    priority: bool = False
    time_charging_in_use: bool = False


def connected_config_factory() -> ConnectedConfig:
    return ConnectedConfig()


def connected_info_factory() -> ConnectedInfo:
    return ConnectedInfo()


def connected_soc_factory() -> ConnectedSoc:
    return ConnectedSoc()


@dataclass
class ConnectedVehicle:
    config: ConnectedConfig = field(default_factory=connected_config_factory)
    info: ConnectedInfo = field(default_factory=connected_info_factory)
    soc: ConnectedSoc = field(default_factory=connected_soc_factory)


@dataclass
class Log:
    chargemode_log_entry: str = "_"
    costs: float = 0
    imported_at_mode_switch: float = 0
    imported_at_plugtime: float = 0
    imported_since_mode_switch: float = 0
    imported_since_plugged: float = 0
    range_charged: float = 0
    time_charged: str = "00:00"
    timestamp_start_charging: Optional[float] = None
    ev: int = -1
    prio: bool = False
    rfid: Optional[str] = None
    serial_number: Optional[str] = None
    soc_at_start: Optional[int] = None
    soc_at_end: Optional[int] = None
    range_at_start: Optional[float] = None
    range_at_end: Optional[float] = None


def connected_vehicle_factory() -> ConnectedVehicle:
    return ConnectedVehicle()


@dataclass
class Get:
    charge_state: bool = False
    charging_current: Optional[float] = 0
    charging_power: Optional[float] = 0
    charging_voltage: Optional[float] = 0
    connected_vehicle: ConnectedVehicle = field(default_factory=connected_vehicle_factory)
    currents: List[float] = field(default_factory=currents_list_factory)
    daily_imported: float = 0
    daily_exported: float = 0
    error_timestamp: int = 0
    evse_current: Optional[float] = None
    exported: float = 0
    fault_str: str = NO_ERROR
    fault_state: int = 0
    imported: float = 0
    max_evse_current: Optional[int] = None
    phases_in_use: int = 0
    plug_state: bool = False
    power: float = 0
    rfid_timestamp: Optional[float] = None
    rfid: Optional[int] = None
    serial_number: Optional[str] = None
    soc: Optional[float] = None
    soc_timestamp: Optional[int] = None
    state_str: Optional[str] = None
    vehicle_id: Optional[str] = None
    voltages: List[float] = field(default_factory=voltages_list_factory)


def ev_factory() -> Ev:
    return Ev(0)


def log_factory() -> Log:
    return Log()


@dataclass
class Set:
    charging_ev: int = -1
    charging_ev_prev: int = -1
    current: float = 0
    energy_to_charge: float = 0
    loadmanagement_available: bool = True
    log: Log = field(default_factory=log_factory)
    manual_lock: bool = False
    phases_to_use: int = 0
    plug_state_prev: bool = False
    plug_time: Optional[float] = None
    required_power: float = 0
    rfid: Optional[str] = None
    # set current aus dem vorherigen Zyklus, um zu wissen, ob am Ende des Zyklus die Ladung freigegeben wird
    # (für Control-Pilot-Unterbrechung)
    current_prev: float = 0.0
    target_current: float = 0  # Soll-Strom aus fest vorgegebener Stromstärke
    charging_ev_data: Ev = field(default_factory=ev_factory)
    ocpp_transaction_id: Optional[int] = None


@dataclass
class Config:
    configuration: Dict = field(default_factory=empty_dict_factory)
    ev: int = 0
    name: str = "neuer Ladepunkt"
    type: Optional[str] = None
    template: int = 0
    connected_phases: int = 3
    phase_1: int = 1
    auto_phase_switch_hw: bool = False
    control_pilot_interruption_hw: bool = False
    id: int = 0
    ocpp_chargebox_id: Optional[str] = None

    def __post_init__(self):
        self.event_update_state: threading.Event

    @property
    def ev(self) -> int:
        return self._ev

    @ev.setter
    def ev(self, ev: int):
        self._ev = ev
        try:
            self.event_update_state.set()
        except AttributeError:
            pass

    def __getstate__(self):
        state = self.__dict__.copy()
        if state.get('event_update_state'):
            del state['event_update_state']
        return state

    def __setstate__(self, state):
        self.__dict__.update(state)


def get_factory() -> Get:
    return Get()


def set_factory() -> Set:
    return Set()


def config_factory() -> Config:
    return Config()


@dataclass
class ChargepointData:
    control_parameter: ControlParameter = field(default_factory=control_parameter_factory)
    get: Get = field(default_factory=get_factory)
    set: Set = field(default_factory=set_factory)
    config: Config = field(default_factory=config_factory)

    def set_event(self, event: Optional[threading.Event] = None) -> None:
        self.event_update_state = event
        if event:
            self.config.event_update_state = event

    def __getstate__(self):
        # Copy the object's state from self.__dict__ which contains
        # all our instance attributes. Always use the dict.copy()
        # method to avoid modifying the original state.
        state = self.__dict__.copy()
        # Remove the unpicklable entries.
        if state.get('event_update_state'):
            del state['event_update_state']
        return state

    def __setstate__(self, state):
        # Restore instance attributes (i.e., filename and lineno).
        self.__dict__.update(state)


class ChargepointProtocol(Protocol):
    @property
    def template(self) -> CpTemplate: ...
    @property
    def chargepoint_module(self) -> AbstractChargepoint: ...
    @property
    def num(self) -> int: ...
    @property
    def data(self) -> ChargepointData: ...
