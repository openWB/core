import logging
from typing import List

from control.algorithm.common import CHARGEMODES
from control.chargepoint import Chargepoint
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
