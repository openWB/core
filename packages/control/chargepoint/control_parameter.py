from dataclasses import dataclass, field
from typing import List, Optional

from control.chargepoint.chargepoint_state import ChargepointState
from control.chargemode import Chargemode as Chargemode_enum
from control.limiting_value import LimitingValue
from dataclass_utils.factories import currents_list_factory


@dataclass
class ControlParameter:
    chargemode: Chargemode_enum = field(default=Chargemode_enum.STOP, metadata={
                                        "topic": "control_parameter/chargemode"})
    current_plan: Optional[str] = field(default=None, metadata={"topic": "control_parameter/current_plan"})
    failed_phase_switches: int = field(default=0, metadata={"topic": "control_parameter/failed_phase_switches"})
    imported_at_plan_start: Optional[float] = field(
        default=None, metadata={"topic": "control_parameter/imported_at_plan_start"})
    imported_instant_charging: Optional[float] = field(
        default=None, metadata={"topic": "control_parameter/imported_instant_charging"})
    limit: Optional[LimitingValue] = field(default=None, metadata={"topic": "control_parameter/limit"})
    min_current: int = field(default=6, metadata={"topic": "control_parameter/min_current"})
    phases: int = field(default=0, metadata={"topic": "control_parameter/phases"})
    prio: bool = field(default=False, metadata={"topic": "control_parameter/prio"})
    required_current: float = field(default=0, metadata={"topic": "control_parameter/required_current"})
    required_currents: List[float] = field(default_factory=currents_list_factory)
    state: ChargepointState = field(default=ChargepointState.NO_CHARGING_ALLOWED,
                                    metadata={"topic": "control_parameter/state"})
    submode: Chargemode_enum = field(default=Chargemode_enum.STOP, metadata={"topic": "control_parameter/submode"})
    timestamp_charge_start: Optional[float] = field(
        default=None, metadata={"topic": "control_parameter/timestamp_charge_start"})
    timestamp_last_phase_switch: float = field(
        default=0, metadata={"topic": "control_parameter/timestamp_last_phase_switch"})
    timestamp_switch_on_off: Optional[float] = field(
        default=None, metadata={"topic": "control_parameter/timestamp_switch_on_off"})


def control_parameter_factory() -> ControlParameter:
    return ControlParameter()
