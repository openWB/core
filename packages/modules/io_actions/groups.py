from enum import Enum


class ActionGroup(Enum):
    CONTROLLABLE_CONSUMERS = "controllable_consumers"
    GENERATOR_SYSTEMS = "generator_systems"


READBALE_GROUP_NAME = {
    ActionGroup.CONTROLLABLE_CONSUMERS: "Steuerbare Verbrauchseinrichtungen (§14a)"
    ActionGroup.GENERATOR_SYSTEMS: "Erzeugungsanlagen"
}
