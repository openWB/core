from typing import Optional
from unittest.mock import Mock

import pytest
from control import data
from control.chargepoint.chargepoint import Chargepoint


@pytest.fixture()
def mock_data() -> None:
    data.data_init(Mock())
    data.data.cp_data["cp1"] = Chargepoint(1, None)
    data.data.cp_data["cp1"].data.get.rfid = "1234"


@pytest.mark.parametrize(
    "partner_id, cp0_plug_state, cp1_plug_state, cp0_plug_time, cp1_plug_time, expected_set_rfid",
    [
        pytest.param(None, True, False, None, None, "1234", id="no duo"),
        pytest.param(1, True, False, None, None, "1234", id="second cp not plugged"),
        pytest.param(1, True, True, 1706868636, 1706868646, None, id="self first plugged"),
        pytest.param(1, True, True, 1706868636, 1706868626, "1234", id="second first plugged"),
        pytest.param(1, False, True, None, 1706868626, None,
                     id="second plugged, self not plugged yet, wait for plugging"),
    ])
def test_link_rfid_to_cp(partner_id: Optional[int],
                         cp0_plug_state: bool,
                         cp1_plug_state: bool,
                         cp0_plug_time: Optional[str],
                         cp1_plug_time: Optional[str],
                         expected_set_rfid: Optional[str],
                         mock_data,
                         monkeypatch):
    # setup
    cp = Chargepoint(0, None)
    cp.chargepoint_module = Mock()
    cp.data.get.rfid = "1234"
    cp.data.get.plug_state = cp0_plug_state
    cp.data.set.plug_time = cp0_plug_time
    data.data.cp_data["cp1"].data.get.plug_state = cp1_plug_state
    data.data.cp_data["cp1"].data.set.plug_time = cp1_plug_time
    mock_find_duo_partner = Mock(return_value=partner_id)
    monkeypatch.setattr(Chargepoint, "find_duo_partner", mock_find_duo_partner)

    # execution
    cp._link_rfid_to_cp()

    # evaluation
    assert cp.data.set.rfid == expected_set_rfid
