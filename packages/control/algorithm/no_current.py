import logging
from typing import List
from control import data

from control.algorithm.common import CHARGEMODES
from control.chargepoint.chargepoint import Chargepoint
from control.algorithm.filter_chargepoints import get_chargepoints_by_mode

log = logging.getLogger(__name__)


class NoCurrent:
    def __init__(self) -> None:
        pass

    def set_no_current(self) -> None:
        chargepoints: List[Chargepoint] = []
        for mode in CHARGEMODES[12:16]:
            chargepoints.extend(get_chargepoints_by_mode(mode))
        for cp in chargepoints:
            cp.data.set.current = 0

    def set_none_current(self) -> None:
        for cp in data.data.cp_data.values():
            if cp.data.set.current is None:
                cp.data.set.current = 0
