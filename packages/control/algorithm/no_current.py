import logging
from control import data

from control.algorithm.chargemodes import CONSIDERED_CHARGE_MODES_NO_CURRENT
from control.algorithm.filter_chargepoints import get_chargepoints_by_chargemodes

log = logging.getLogger(__name__)


class NoCurrent:
    def __init__(self) -> None:
        pass

    def set_no_current(self) -> None:
        chargepoints = get_chargepoints_by_chargemodes(CONSIDERED_CHARGE_MODES_NO_CURRENT)
        for cp in chargepoints:
            cp.data.set.current = 0

    def set_none_current(self) -> None:
        for cp in data.data.cp_data.values():
            if cp.data.set.current is None:
                cp.data.set.current = 0
