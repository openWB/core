from enum import IntEnum


class StateMachine(IntEnum):
    NO_CHARGING_ALLOWED = 0
    PHASE_SWITCH_DELAY = 1
    PERFORMING_PHASE_SWITCH = 2
    WAIT_FOR_USING_PHASES = 3
    CHARGING_ALLOWED = 4
    SWITCH_OFF_DELAY = 5
    SWITCH_ON_DELAY = 6
    PHASE_SWITCH_DELAY_EXPIRED = 7


CHARGING_STATES = (StateMachine.PHASE_SWITCH_DELAY,
                   StateMachine.WAIT_FOR_USING_PHASES,
                   StateMachine.CHARGING_ALLOWED,
                   StateMachine.SWITCH_OFF_DELAY,
                   StateMachine.PHASE_SWITCH_DELAY_EXPIRED)

PHASE_SWITCH_STATES = (StateMachine.PHASE_SWITCH_DELAY,
                       StateMachine.PERFORMING_PHASE_SWITCH,
                       StateMachine.WAIT_FOR_USING_PHASES)
