from enum import Enum


class ActionGroup(Enum):
    CONTROLLABLE_CONSUMERS = "controllable_consumers"
    PRODUCTION_PLANTS = "production_plants"


READABLE_GROUP_NAME = {
    ActionGroup.CONTROLLABLE_CONSUMERS: "Steuerbare Verbrauchseinrichtungen (§14a)",
    ActionGroup.PRODUCTION_PLANTS: "Erzeugungsanlagen (§9)",
}
