from typing import Optional
import pytest

from control.algorithm import Algorithm


class Params:
    def __init__(self,
                 name: str,
                 chargemode: Optional[str],
                 submode: str,
                 prio: bool,
                 index: int) -> None:
        self.name = name
        self.chargemode = chargemode
        self.submode = submode
        self.prio = prio
        self.index = index


cases = [
    Params("instant prio", "instant_charging", "instant_charging", True, 4),
    Params("stop no prio", None, "stop", False, 15)
]


@pytest.mark.parametrize("params", cases, ids=[c.name for c in cases])
def test_mode_index(params: Params):
    # setup, execution and evaluation
    assert Algorithm()._get_mode_index(params.chargemode, params.submode, params.prio) == params.index
