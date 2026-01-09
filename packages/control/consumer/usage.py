from enum import Enum


class ConsumerUsage(Enum):
    METER_ONLY = "meter_only"
    SUSPENDABLE_TUNABLE = "suspendable_tunable"
    SUSPENDABLE_TUNABLE_INDIVIDUAL = "suspendable_tunable_individual"
    SUSPENDABLE_ONOFF = "suspendable_onoff"
    SUSPENDABLE_ONOFF_INDIVIDUAL = "suspendable_onoff_individual"
    CONTINUOUS = "continuous"
