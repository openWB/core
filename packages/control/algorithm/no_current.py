import logging
from control import data

from control.algorithm.chargemodes import CONSIDERED_CHARGE_MODES_NO_CURRENT
from control.algorithm.filter_chargepoints import get_chargepoints_by_chargemode
from control.chargepoint.chargepoint_state import ChargepointState

log = logging.getLogger(__name__)


class NoCurrent:
    def __init__(self) -> None:
        pass

    def set_no_current(self) -> None:
        chargepoints = get_chargepoints_by_chargemode(CONSIDERED_CHARGE_MODES_NO_CURRENT)
        for cp in chargepoints:
            cp.data.set.current = 0
            cp.data.control_parameter.state = ChargepointState.NO_CHARGING_ALLOWED

    def set_none_current(self) -> None:
        for cp in data.data.cp_data.values():
            if cp.data.set.current is None:
                cp.data.set.current = 0
