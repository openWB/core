"""YourCharge Daten
"""
import logging

from typing import List
from enum import Enum

from dataclasses import dataclass, field
from dataclass_utils.factories import empty_list_factory


yc_root_topic = 'yourCharge'
yc_status_topic = yc_root_topic + '/status'
yc_control_topic = yc_root_topic + '/control'
yc_config_topic = yc_root_topic + '/config'
yc_socket_activated_topic = yc_control_topic + '/socket_activated'
yc_socket_requested_topic = yc_control_topic + '/socket_request'


# load management states that we can be in
class LmStatus(int, Enum):
    Superseded = 0
    InLoop = 1
    DownByLm = 2
    DownByEv = 3
    DownByError = 4
    DownByDisable = 5
    # 6-7 reserved for LM use
    DownForSocket = 8
    DownByEnergyLimit = 9


# standard socket control actions
class StandardSocketActions(str, Enum):
    # Uninitialized default value. Don't use.
    Uninitialized = "Uninitialized"

    # Approve socket usage.
    Approve = "Approve"

    # Explicitly decline socket usage.
    # This shall be used only if socket has been requested and cannot be granted.
    # Once granted and socket needs to be disabled (e.g. for load control reasons), use "TurnOff".
    Decline = "Decline"

    # Request immediate turn off of the socket.
    # Use this action if socket use had been granted but socket now needs to be turned off (e.g. for load control reasons).
    # To reject an activation request, use "Decline" as this allows more detailed feedback to user.
    TurnOff = "TurnOff"


class SocketRequestStates(str, Enum):
    # Socket request state is uninitialized.
    Uninitialized = "Uninitialized"

    # No specific socket request.
    NoRequest = "NoRequest"

    # Turning ON of socket has been requested.
    OnRequested = "OnRequested"

    # Turning OFF of socket has been requested.
    OffRequested = "OffRequested"


log = logging.getLogger(__name__)

def three_zero_ints_factory() -> List[int]:
    return [ 0, 0, 0 ]

def three_zero_floatss_factory() -> List[float]:
    return [ 0.0, 0.0, 0.0 ]

@dataclass
class YcConfig:
    active: bool = False
    allowed_rfid_ev: List[str] = field(default_factory=empty_list_factory)
    allowed_rfid_std_socket: List[str] = field(default_factory=empty_list_factory)
    allowed_peak_power: float = None
    allowed_total_current_per_phase: float = None
    allowed_load_imbalance: float = None
    max_evse_current_allowed: float = None
    min_evse_current_allowed: float = None
    minimum_adjustment_interval: int = None
    slow_ramping: bool = None
    standard_socket_installed: bool = None
    use_last_charging_phase: bool = None
    box_id: str = None

@dataclass
class YcControlData:
    def __init__(self):
        self._fixed_charge_current = 0.0

    charging_vehicles: List[int] = field(default_factory=three_zero_ints_factory)
    total_current_consumption: List[float] = field(default_factory=three_zero_floatss_factory)
    total_power: float = None
    imbalance_current_consumption: List[float] = field(default_factory=three_zero_floatss_factory)
    standard_socket_action: StandardSocketActions = StandardSocketActions.Uninitialized
    socket_request: SocketRequestStates = SocketRequestStates.Uninitialized
    cp_enabled: bool = False
    socket_activated: bool = False

    @property
    def fixed_charge_current(self) -> float:
        return self._fixed_charge_current

    @fixed_charge_current.setter
    def fixed_charge_current(self, value):
        if value is None or float(value) < 0:
            self._fixed_charge_current = None
        else:
            self._fixed_charge_current = float(value)


@dataclass
class YcData:
    def __init__(self):
        self._yc_config = YcConfig()
        self._yc_control = YcControlData()
        self._last_controller_publish = 0

    @property
    def yc_config(self) -> YcConfig:
        return self._yc_config

    @property
    def yc_control(self) -> YcControlData:
        return self._yc_control

    @property
    def last_controller_publish(self) -> int:
        return self._last_controller_publish

    @last_controller_publish.setter
    def last_controller_publish(self, value):
        try:
            intvalue = int(value)
            if intvalue < 0:
                self._last_controller_publish = 0
            else:
                self._last_controller_publish = intvalue
        except:
            self._last_controller_publish = 0


# All YourCharge data
class YourCharge:
    """Config and data for use by YourCharge charge system algorithms
    """

    def __init__(self):
        self.data: YcData = YcData()
