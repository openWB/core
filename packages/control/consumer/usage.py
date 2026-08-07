from enum import Enum


class ConsumerUsage(Enum):
    METER_ONLY = "meter_only"
    SELF_CONTROLLED = "self_controlled"
    SUSPENDABLE_TUNABLE = "suspendable_tunable"
    SUSPENDABLE_ONOFF = "suspendable_onoff"
    CONTINUOUS = "continuous"


NOT_CONTROLLED = (ConsumerUsage.METER_ONLY, ConsumerUsage.SELF_CONTROLLED)
