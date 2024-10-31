from enum import Enum


class ActionGroup(Enum):
    CONTROLLABLE_CONSUMERS = "controllable_consumers"


READBALE_GROUP_NAME = {
    ActionGroup.CONTROLLABLE_CONSUMERS: "Steuerbare Verbrauchseinrichtungen (§14a)"
}
