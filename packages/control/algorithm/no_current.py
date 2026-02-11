import logging
from control import data

from control.algorithm.chargemodes import CONSIDERED_CHARGE_MODES_NO_CURRENT
from control.algorithm.filter_chargepoints import get_loadmanagement_prios

log = logging.getLogger(__name__)


class NoCurrent:
    def __init__(self) -> None:
        pass

    def set_no_current(self) -> None:
        chargepoints = get_loadmanagement_prios(CONSIDERED_CHARGE_MODES_NO_CURRENT)
        for cp in chargepoints:
            cp.data.set.current = 0

    def set_none_current(self) -> None:
        for load in list(data.data.cp_data.values()) + list(data.data.consumer_data.values()):
            if load.data.set.current is None:
                load.data.set.current = 0
