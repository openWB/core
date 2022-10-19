from typing import Dict, NamedTuple, Optional
from unittest.mock import Mock

import pytest

from control.chargepoint import Autolock, CpTemplate, CpTemplateData
from helpermodules import timecheck

template_params = NamedTuple("template_params", [("name", str),
                                                 ("active", bool),
                                                 ("plans", Dict),
                                                 ("mock_timecheck", Optional[Dict]),
                                                 ("wait_for_charging_end", bool),
                                                 ("charge_state", bool),
                                                 ("expected_return", bool)])

cases = [
    template_params("autolock inactive", False, {}, None, False, False, False),
    template_params("autolock no plans active", True, {0: "Plan"}, None, False, True, False),
    template_params("autolock no plans", True, {}, None, False, False, False),
    template_params("autolock stop immediately", True, {0: "Plan"}, {0: "Plan"}, False, True, True),
    template_params("autolock stop after charging end", True, {0: "Plan"}, {0: "Plan"}, True, True, False),
    template_params("autolock stop after charging end(stopped)", True, {0: "Plan"}, {0: "Plan"}, True, False, True),
]


@pytest.mark.parametrize("params", cases, ids=[c.name for c in cases])
def test_is_locked_by_autolock(monkeypatch, params: template_params):
    # setup
    cpt = CpTemplate()
    cpt.data = Mock(spec=CpTemplateData, autolock=Mock(spec=Autolock,
                                                       active=params.active,
                                                       plans=params.plans,
                                                       wait_for_charging_end=params.wait_for_charging_end))
    monkeypatch.setattr(timecheck, "check_plans_timeframe", Mock(return_value=params.mock_timecheck))

    # execution
    locked = cpt.is_locked_by_autolock(params.charge_state)

    # evaluation
    assert locked == params.expected_return
