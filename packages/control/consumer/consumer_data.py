from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Union
from control.chargepoint.control_parameter import ControlParameter, control_parameter_factory
from control.consumer.usage import ConsumerUsage
from dataclass_utils.factories import empty_list_factory
from helpermodules.abstract_plans import (ContinuousConsumerPlan, SuspendableOnOffConsumerPlan,
                                          SuspendableTunableConsumerPlan)
from helpermodules.constants import NO_ERROR
from modules.common.consumer_setup import ConsumerSetup


def get_meter_only_config() -> Dict:
    return MeterOnlyConfig()


@dataclass
class MeterOnlyConfig:
    type: ConsumerUsage = ConsumerUsage.METER_ONLY


def get_suspendable_tunable_consumer_config() -> Dict:
    return SuspendableTunableDeviceConfig()


def get_suspendable_tunable_consumer_individual_config() -> Dict:
    return SuspendableTunableDeviceConfig(type=ConsumerUsage.SUSPENDABLE_TUNABLE_INDIVIDUAL)


@dataclass
class SuspendableTunableDeviceConfig:
    min_current: int = 0.5
    min_intervall: int = 60
    plans: List[SuspendableTunableConsumerPlan] = field(default_factory=empty_list_factory)
    price_limit_active: bool = False
    price_limit: float = 0.07
    type: ConsumerUsage = ConsumerUsage.SUSPENDABLE_TUNABLE


def get_suspendable_onoff_consumer_config() -> Dict:
    return SuspendableOnOffDeviceConfig()


def get_suspendable_onoff_consumer_individual_config() -> Dict:
    return SuspendableOnOffDeviceConfig(type=ConsumerUsage.SUSPENDABLE_ONOFF_INDIVIDUAL)


@dataclass
class SuspendableOnOffDeviceConfig:
    min_current: int = 0.5
    min_intervall: int = 60
    plans: List[SuspendableOnOffConsumerPlan] = field(default_factory=empty_list_factory)
    price_limit_active: bool = False
    price_limit: float = 0.07
    type: ConsumerUsage = ConsumerUsage.SUSPENDABLE_ONOFF


def get_continuous_consumer_config() -> Dict:
    return ContinuousDeviceConfig()


@dataclass
class ContinuousDeviceConfig:
    min_current: int = 0.5
    min_intervall: int = 2*60*60
    wait_for_start_active: bool = True
    wait_for_start_signal: bool = False
    wait_for_start_test: bool = False
    wait_for_start_last_test_timestamp: float = 0
    plans: List[ContinuousConsumerPlan] = field(default_factory=empty_list_factory)
    price_limit_active: bool = False
    price_limit: float = 0.07
    type: ConsumerUsage = ConsumerUsage.CONTINUOUS


GET_DEFAULTS_BY_USAGE: Dict[ConsumerUsage, callable] = {
    ConsumerUsage.METER_ONLY: get_meter_only_config,
    ConsumerUsage.SUSPENDABLE_TUNABLE: get_suspendable_tunable_consumer_config,
    ConsumerUsage.SUSPENDABLE_TUNABLE_INDIVIDUAL: get_suspendable_tunable_consumer_individual_config,
    ConsumerUsage.SUSPENDABLE_ONOFF: get_suspendable_onoff_consumer_config,
    ConsumerUsage.SUSPENDABLE_ONOFF_INDIVIDUAL: get_suspendable_onoff_consumer_individual_config,
    ConsumerUsage.CONTINUOUS: get_continuous_consumer_config,
}

GET_CLASS_BY_USAGE: Dict[ConsumerUsage, Callable] = {
    ConsumerUsage.METER_ONLY: MeterOnlyConfig,
    ConsumerUsage.SUSPENDABLE_TUNABLE: SuspendableTunableDeviceConfig,
    ConsumerUsage.SUSPENDABLE_TUNABLE_INDIVIDUAL: SuspendableTunableDeviceConfig,
    ConsumerUsage.SUSPENDABLE_ONOFF: SuspendableOnOffDeviceConfig,
    ConsumerUsage.SUSPENDABLE_ONOFF_INDIVIDUAL: SuspendableOnOffDeviceConfig,
    ConsumerUsage.CONTINUOUS: ContinuousDeviceConfig,
}


def get_plan_class_for_usage(usage: ConsumerUsage):
    if usage == ConsumerUsage.CONTINUOUS:
        return ContinuousConsumerPlan
    elif usage in [ConsumerUsage.SUSPENDABLE_TUNABLE, ConsumerUsage.SUSPENDABLE_TUNABLE_INDIVIDUAL]:
        return SuspendableTunableConsumerPlan
    elif usage in [ConsumerUsage.SUSPENDABLE_ONOFF, ConsumerUsage.SUSPENDABLE_ONOFF_INDIVIDUAL]:
        return SuspendableOnOffConsumerPlan
    else:
        return None


@dataclass
class ConsumerConfig:
    connected_phases: int = 1
    phase_1: int = 1
    max_power: float = 5000


def consumer_config_factory() -> ConsumerConfig:
    return ConsumerConfig()


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


def get_factory() -> Get:
    return Get()


@dataclass
class Set:
    current: float = 0
    loadmanagement_available: bool = False
    phases_to_use: int = 0
    plug_time: Optional[float] = 0
    required_power: float = 0
    current_prev: float = 0
    target_current: float = 0
    charge_state_prev: bool = False
    power: Optional[float] = None
    timestamp_last_current_set: float = field(default=0, metadata={"topic": "set/timestamp_last_current_set"})


def set_factory() -> Set:
    return Set()


@dataclass
class ExtraMeterConfig:
    device: Optional[Dict] = None
    component: Optional[Dict] = None


def extra_meter_config_factory() -> ExtraMeterConfig:
    return ExtraMeterConfig()


@dataclass
class ConsumerData:
    module: ConsumerSetup = None
    config: ConsumerConfig = field(default_factory=consumer_config_factory)
    extra_meter: ExtraMeterConfig = field(default_factory=extra_meter_config_factory)
    usage: Union[MeterOnlyConfig, SuspendableTunableDeviceConfig,
                 SuspendableOnOffDeviceConfig, ContinuousDeviceConfig] = field(default_factory=get_meter_only_config)
    control_parameter: ControlParameter = field(default_factory=control_parameter_factory)
    get: Get = field(default_factory=get_factory)
    set: Set = field(default_factory=set_factory)
