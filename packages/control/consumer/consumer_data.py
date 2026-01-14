from dataclasses import asdict, dataclass, field
from typing import Dict, List, Optional, Union
from control.chargepoint.control_parameter import ControlParameter, control_parameter_factory
from control.consumer.usage import ConsumerUsage
from dataclass_utils.factories import empty_list_factory
from helpermodules.abstract_plans import ContinuousConsumerPlan, SuspendableConsumerPlan
from helpermodules.constants import NO_ERROR
from modules.common.consumer_setup import ConsumerSetup


def get_meter_only_config() -> Dict:
    return asdict(MeterOnlyConfig())


@dataclass
class MeterOnlyConfig:
    type: ConsumerUsage = ConsumerUsage.METER_ONLY


def get_suspendable_tunable_consumer_config() -> Dict:
    return asdict(SuspendableTunableDeviceConfig())


def get_suspendable_tunable_consumer_individual_config() -> Dict:
    return asdict(SuspendableTunableDeviceConfig(type=ConsumerUsage.SUSPENDABLE_TUNABLE_INDIVIDUAL))


@dataclass
class SuspendableTunableDeviceConfig:
    min_current: int = 0.5
    min_intervall: int = 60
    plans: List[SuspendableConsumerPlan] = field(default_factory=empty_list_factory)
    price_limit: float = 0.07
    type: ConsumerUsage = ConsumerUsage.SUSPENDABLE_TUNABLE


def get_suspendable_onoff_consumer_config() -> Dict:
    return asdict(SuspendableOnOffDeviceConfig())


def get_suspendable_onoff_consumer_individual_config() -> Dict:
    return asdict(SuspendableOnOffDeviceConfig(type=ConsumerUsage.SUSPENDABLE_ONOFF_INDIVIDUAL))


@dataclass
class SuspendableOnOffDeviceConfig:
    min_current: int = 0.5
    min_intervall: int = 60
    plans: List[SuspendableConsumerPlan] = field(default_factory=empty_list_factory)
    price_limit: float = 0.07
    type: ConsumerUsage = ConsumerUsage.SUSPENDABLE_ONOFF


def get_continuous_consumer_config() -> Dict:
    return asdict(ContinuousDeviceConfig())


@dataclass
class ContinuousDeviceConfig:
    min_current: int = 0.5
    min_intervall: int = 2*60*60
    wait_for_start_active: bool = True
    plans: List[ContinuousConsumerPlan] = field(default_factory=empty_list_factory)
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


def get_plan_class_for_usage(usage: ConsumerUsage):
    if usage == ConsumerUsage.CONTINUOUS:
        return ContinuousConsumerPlan
    elif usage in [ConsumerUsage.SUSPENDABLE_TUNABLE, ConsumerUsage.SUSPENDABLE_ONOFF,
                   ConsumerUsage.SUSPENDABLE_TUNABLE_INDIVIDUAL, ConsumerUsage.SUSPENDABLE_ONOFF_INDIVIDUAL]:
        return SuspendableConsumerPlan
    else:
        return None


@dataclass
class ConsumerConfig:
    connected_phases: int = 3
    phase_1: int = 1


def consumer_config_factory() -> ConsumerConfig:
    return ConsumerConfig()


@dataclass
class Get:
    fault_str: str = NO_ERROR
    fault_state: int = 0
    imported: float = 0
    exported: float = 0
    power: float = 0
    voltages: Optional[List[Optional[float]]] = None
    currents: Optional[List[Optional[float]]] = None
    powers: Optional[List[Optional[float]]] = None
    set_power: Optional[float] = None
    state: Optional[bool] = False


def get_factory() -> Get:
    return Get()


@dataclass
class Set:
    state_str: Optional[str] = None
    timestamp_last_current_set: float = 0


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
                 SuspendableOnOffDeviceConfig, ContinuousDeviceConfig] = None
    control_parameter: ControlParameter = field(default_factory=control_parameter_factory)
    get: Get = field(default_factory=get_factory)
    set: Set = field(default_factory=set_factory)
