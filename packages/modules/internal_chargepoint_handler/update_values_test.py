import copy
from unittest.mock import Mock
import pytest

from modules.common.component_state import ChargepointState
from modules.conftest import SAMPLE_IP
from modules.internal_chargepoint_handler.internal_chargepoint_handler import UpdateValues
from modules.internal_chargepoint_handler import internal_chargepoint_handler

CHARGEPOINT_STATE = ChargepointState(
    power=1430,
    currents=[6]*3,
    imported=100,
    exported=0,
    voltages=[230]*3,
    plug_state=True,
    charge_state=True,
    phases_in_use=3,
    rfid="2")

OLD_CHARGEPOINT_STATE = copy.deepcopy(CHARGEPOINT_STATE)
OLD_CHARGEPOINT_STATE.imported = 80


@pytest.mark.parametrize(
    "old_chargepoint_state, published_topics",
    [(None, 44),
     (OLD_CHARGEPOINT_STATE, 2)]

)
def test_update_values(old_chargepoint_state, published_topics, monkeypatch):
    # setup
    mock_pub_single = Mock()
    monkeypatch.setattr(internal_chargepoint_handler, "pub_single", mock_pub_single)
    u = UpdateValues(0, SAMPLE_IP, "1", 1)
    u.old_chargepoint_state = old_chargepoint_state

    # execution
    u.update_values(CHARGEPOINT_STATE, False)

    # evaluation
    assert mock_pub_single.call_count == published_topics
