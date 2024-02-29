from dataclasses import dataclass, field
from typing import List, Optional

from control.chargepoint.chargepoint_state import ChargepointState
from control.chargemode import Chargemode as Chargemode_enum
from control.limiting_value import LimitingValue
from dataclass_utils.factories import currents_list_factory


@dataclass
class ControlParameter:
    chargemode: Chargemode_enum = field(
        default=Chargemode_enum.STOP,
        metadata={"topic": "control_parameter/chargemode", "mutable_by_algorithm": True})
    current_plan: Optional[str] = field(
        default=None,
        metadata={"topic": "control_parameter/current_plan", "mutable_by_algorithm": True})
    failed_phase_switches: int = field(
        default=0,
        metadata={"topic": "control_parameter/failed_phase_switches", "mutable_by_algorithm": True})
    imported_at_plan_start: Optional[float] = field(
        default=None,
        metadata={"topic": "control_parameter/imported_at_plan_start", "mutable_by_algorithm": True})
    imported_instant_charging: Optional[float] = field(
        default=None,
        metadata={"topic": "control_parameter/imported_instant_charging", "mutable_by_algorithm": True})
    limit: Optional[LimitingValue] = field(
        default=None,
        metadata={"topic": "control_parameter/limit", "mutable_by_algorithm": True})
    phases: int = field(
        default=0,
        metadata={"topic": "control_parameter/phases", "mutable_by_algorithm": True})
    prio: bool = field(
        default=False,
        metadata={"topic": "control_parameter/prio", "mutable_by_algorithm": True})
    required_current: float = field(
        default=0,
        metadata={"topic": "control_parameter/required_current", "mutable_by_algorithm": True})
    required_currents: List[float] = field(
        default_factory=currents_list_factory)
    state: ChargepointState = field(
        default=ChargepointState.NO_CHARGING_ALLOWED,
        metadata={"topic": "control_parameter/state", "mutable_by_algorithm": True})
    submode: Chargemode_enum = field(
        default=Chargemode_enum.STOP,
        metadata={"topic": "control_parameter/submode", "mutable_by_algorithm": True})
    timestamp_auto_phase_switch: Optional[float] = field(
        default=None,
        metadata={"topic": "control_parameter/timestamp_auto_phase_switch", "mutable_by_algorithm": True})
    timestamp_perform_phase_switch: Optional[float] = field(
        default=None,
        metadata={"topic": "control_parameter/timestamp_perform_phase_switch", "mutable_by_algorithm": True})
    timestamp_switch_on_off: Optional[float] = field(
        default=None,
        metadata={"topic": "control_parameter/timestamp_switch_on_off", "mutable_by_algorithm": True})


def control_parameter_factory() -> ControlParameter:
    return ControlParameter()
