import logging
import math
from typing import Iterable, List, Union

from modules.common.modbus import Number

log = logging.getLogger(__name__)

# Registers that are not applicable to a meter class return the unsupported value. (e.g. Single Phase
# meters will support only summary and phase A values):

UINT16_UNSUPPORTED = 0xFFFF


def scale_registers(registers: Union[List[Number], Number], scale: float) -> List[float]:
    log.debug("Registers %s, Scale %s", registers, scale)
    if not isinstance(registers, Iterable):
        return registers * math.pow(10, scale) if registers != UINT16_UNSUPPORTED else 0
    else:
        return [register * math.pow(10, scale) if register != UINT16_UNSUPPORTED else 0 for register in registers]
