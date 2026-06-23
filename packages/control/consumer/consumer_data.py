from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Dict, List, Optional, Union
from control.chargemode import Chargemode
from control.chargepoint.control_parameter import ControlParameter, control_parameter_factory
from control.consumer.usage import ConsumerUsage
from dataclass_utils.factories import empty_list_factory
from helpermodules.abstract_plans import (ContinuousScheduledPlanConsumer, SuspendableScheduledPlanConsumer,
                                          TimeChargingPlanConsumer)
from helpermodules.constants import NO_ERROR
from modules.common.consumer_setup import ConsumerSetup


@dataclass
class EcoCharging:
    price_limit: float = 0.07


@dataclass
class ScheduledContinuousCharging:
    plans: List[ContinuousScheduledPlanConsumer] = field(default_factory=empty_list_factory)


@dataclass
class ScheduledSuspendableCharging:
    plans: List[SuspendableScheduledPlanConsumer] = field(default_factory=empty_list_factory)


@dataclass
class TimeCharging:
    active: bool = False
    plans: List[TimeChargingPlanConsumer] = field(default_factory=empty_list_factory)


class WaitForStartStates(Enum):
    WAIT_FOR_DEVICE_START = "wait_for_device_start"
    WAIT_FOR_STOPPED_DEVICE = "wait_for_stopped_device"
    DEVICE_WAITING_FOR_START = "device_waiting_for_start"
    START_SIGNAL_RECEIVED = "start_signal_received"


class ResetModes(Enum):
    NEVER = "never"
    MIDNIGHT = "midnight"
    TIME = "time"


@dataclass
class ResetChargemode:
    mode: ResetModes = ResetModes.NEVER
    time: Optional[int] = None
    chargemode: Chargemode = Chargemode.INSTANT_CHARGING


@dataclass
class Log:
    on_time: float = 0


@dataclass
class MeterOnlyConfig:
    type: ConsumerUsage = ConsumerUsage.METER_ONLY


@dataclass
class SuspendableTunableDeviceConfig:
    chargemode: Chargemode = Chargemode.INSTANT_CHARGING
    eco_charging: EcoCharging = field(default_factory=lambda: EcoCharging())
    scheduled_charging: ScheduledSuspendableCharging = field(default_factory=lambda: ScheduledSuspendableCharging())
    time_charging: TimeCharging = field(default_factory=lambda: TimeCharging())
    type: ConsumerUsage = ConsumerUsage.SUSPENDABLE_TUNABLE
    wait_for_start_active: bool = True


@dataclass
class SuspendableOnOffDeviceConfig:
    chargemode: Chargemode = Chargemode.INSTANT_CHARGING
    eco_charging: EcoCharging = field(default_factory=lambda: EcoCharging())
    scheduled_charging: ScheduledSuspendableCharging = field(default_factory=lambda: ScheduledSuspendableCharging())
    time_charging: TimeCharging = field(default_factory=lambda: TimeCharging())
    type: ConsumerUsage = ConsumerUsage.SUSPENDABLE_ONOFF
    wait_for_start_active: bool = True


@dataclass
class ContinuousDeviceConfig:
    chargemode: Chargemode = Chargemode.INSTANT_CHARGING
    eco_charging: EcoCharging = field(default_factory=lambda: EcoCharging())
    scheduled_charging: ScheduledContinuousCharging = field(default_factory=lambda: ScheduledContinuousCharging())
    time_charging: TimeCharging = field(default_factory=lambda: TimeCharging())
    type: ConsumerUsage = ConsumerUsage.CONTINUOUS
    wait_for_start_active: bool = True
    reset_chargemode: ResetChargemode = field(default_factory=lambda: ResetChargemode())


GET_DEFAULTS_BY_USAGE: Dict[ConsumerUsage, Union[MeterOnlyConfig,
                                                 SuspendableTunableDeviceConfig,
                                                 SuspendableOnOffDeviceConfig,
                                                 ContinuousDeviceConfig]] = {
    ConsumerUsage.METER_ONLY: MeterOnlyConfig(),
    ConsumerUsage.SUSPENDABLE_TUNABLE: SuspendableTunableDeviceConfig(),
    ConsumerUsage.SUSPENDABLE_ONOFF: SuspendableOnOffDeviceConfig(),
    ConsumerUsage.CONTINUOUS: ContinuousDeviceConfig(),
}

GET_CLASS_BY_USAGE: Dict[ConsumerUsage, Callable] = {
    ConsumerUsage.METER_ONLY: MeterOnlyConfig,
    ConsumerUsage.SUSPENDABLE_TUNABLE: SuspendableTunableDeviceConfig,
    ConsumerUsage.SUSPENDABLE_ONOFF: SuspendableOnOffDeviceConfig,
    ConsumerUsage.CONTINUOUS: ContinuousDeviceConfig,
}

get_plan_class_for_usage: Dict[ConsumerUsage, Callable] = {
    ConsumerUsage.SUSPENDABLE_TUNABLE: SuspendableScheduledPlanConsumer,
    ConsumerUsage.SUSPENDABLE_ONOFF: SuspendableScheduledPlanConsumer,
    ConsumerUsage.CONTINUOUS: ContinuousScheduledPlanConsumer,
}


@dataclass
class ConsumerConfig:
    connected_phases: int = 1
    phase_1: int = 1
    max_power: float = 5000
    min_current: float = 0.5
    min_intervall: int = 60


@dataclass
class Get:
    charge_state: bool = False
    currents: Optional[List[Optional[float]]] = None
    daily_imported: float = field(default=0, metadata={"topic": "get/daily_imported"})
    error_timestamp: int = 0
    exported: float = 0
    fault_str: str = NO_ERROR
    fault_state: int = 0
    imported: float = 0
    phases_in_use: int = 0
    power: float = 0
    powers: Optional[List[Optional[float]]] = None
    set_power: Optional[float] = None
    state: Optional[bool] = False
    state_str: Optional[str] = field(default=None, metadata={"topic": "get/state_str"})
    voltages: Optional[List[Optional[float]]] = None


@dataclass
class Set:
    current: float = field(default=0, metadata={"topic": "set/current"})
    loadmanagement_available: bool = False
    phases_to_use: int = field(default=1, metadata={"topic": "set/phases_to_use"})
    plug_time: Optional[float] = field(default=None, metadata={"topic": "set/plug_time"})
    required_power: float = 0
    current_prev: float = 0
    target_current: float = 0
    charge_state_prev: bool = False
    log: Log = field(default_factory=lambda: Log())
    power: Optional[float] = None
    timestamp_last_current_set: float = field(default=0, metadata={"topic": "set/timestamp_last_current_set"})
    wait_for_start_state: WaitForStartStates = field(
        default=WaitForStartStates.WAIT_FOR_DEVICE_START, metadata={"topic": "set/wait_for_start_state"})


@dataclass
class ConsumerData:
    module: ConsumerSetup = None
    config: ConsumerConfig = field(default_factory=lambda: ConsumerConfig())
    extra_meter: Optional[int] = None
    usage: Union[MeterOnlyConfig,
                 SuspendableTunableDeviceConfig,
                 SuspendableOnOffDeviceConfig,
                 ContinuousDeviceConfig] = field(default_factory=lambda: MeterOnlyConfig())
    control_parameter: ControlParameter = field(default_factory=control_parameter_factory)
    get: Get = field(default_factory=lambda: Get())
    set: Set = field(default_factory=lambda: Set())
