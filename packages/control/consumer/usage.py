from enum import Enum


class ConsumerUsage(Enum):
    METER_ONLY = "meter_only"
    SUSPENDABLE_TUNABLE = "suspendable_tunable"
    SUSPENDABLE_ONOFF = "suspendable_onoff"
    CONTINUOUS = "continuous"
