from enum import IntEnum


class ChargepointState(IntEnum):
    NO_CHARGING_ALLOWED = 0
    PHASE_SWITCH_DELAY = 1
    PERFORMING_PHASE_SWITCH = 2
    WAIT_FOR_USING_PHASES = 3
    CHARGING_ALLOWED = 4
    SWITCH_OFF_DELAY = 5
    SWITCH_ON_DELAY = 6
    PHASE_SWITCH_DELAY_EXPIRED = 7


CHARGING_STATES = (ChargepointState.PHASE_SWITCH_DELAY,
                   ChargepointState.WAIT_FOR_USING_PHASES,
                   ChargepointState.CHARGING_ALLOWED,
                   ChargepointState.SWITCH_OFF_DELAY,
                   ChargepointState.PHASE_SWITCH_DELAY_EXPIRED)

PHASE_SWITCH_STATES = (ChargepointState.PHASE_SWITCH_DELAY,
                       ChargepointState.PERFORMING_PHASE_SWITCH,
                       ChargepointState.WAIT_FOR_USING_PHASES)
