from unittest.mock import Mock
import pytest

from control.chargepoint import Chargepoint
from control import data
from control.counter import Counter
from modules.common.fault_state import FaultStateLevel


@pytest.fixture(autouse=True)
def cp() -> None:
    data.data_init(Mock())
    data.data.cp_data = {"cp0": Chargepoint(0, None), "1": Chargepoint(1, None)}


@pytest.mark.parametrize("fault_state, expected_loadmanagement_available",
                         [pytest.param(FaultStateLevel.ERROR, False),
                          pytest.param(FaultStateLevel.NO_ERROR, True)])
def test_set_loadmanagement_state(fault_state: FaultStateLevel, expected_loadmanagement_available: bool, monkeypatch):
    # setup
    connected_cps_mock = Mock(return_value=["cp0", "cp1"])
    monkeypatch.setattr(data.data.counter_all_data, "get_chargepoints_of_counter", connected_cps_mock)
    counter = Counter(0)
    counter.data["get"]["fault_state"] = fault_state

    # execution
    counter._set_loadmanagement_state()

    # evaluation
    assert data.data.cp_data["cp0"].data.set.loadmanagement_available == expected_loadmanagement_available
    assert data.data.cp_data["cp1"].data.set.loadmanagement_available == expected_loadmanagement_available
