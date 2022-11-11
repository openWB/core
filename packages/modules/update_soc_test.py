from typing import List, Optional, Tuple
from unittest.mock import Mock

import pytest

from control import data
from control.chargepoint import Chargepoint, Get, Set
from control.ev import Ev, EvTemplate
from modules.tesla.soc import Soc
from modules.update_soc import UpdateSoc


@pytest.fixture(autouse=True)
def mock_data() -> None:
    data.data_init(Mock())
    data.data.cp_data["cp0"] = Mock(spec=Chargepoint,
                                    id=id,
                                    chargepoint_module=Mock(),
                                    data=Mock(
                                        get=Mock(spec=Get),
                                        set=Mock(spec=Set)))


@pytest.mark.parametrize(
    "ev_num, set_charge_state, plug_state, plug_state_prev, expected_charge_state, expected_plugged_in",
    [
        pytest.param(1, False, False, False, False, False, id="ev not matched to cp"),
        pytest.param(0, False, False, False, False, False, id="ev not plugged in"),
        pytest.param(0, False, True, False, False, True, id="ev recently plugged in"),
        pytest.param(0, False, True, True, False, False, id="ev plugged in, not charging"),
        pytest.param(0, True, True, True, True, False, id="ev plugged in and charging"),
    ])
def test_get_ev_state(ev_num: int,
                      set_charge_state: bool,
                      plug_state: bool,
                      plug_state_prev: bool,
                      expected_charge_state: bool,
                      expected_plugged_in: bool):
    # setup
    data.data.cp_data["cp0"].data.set.charging_ev = ev_num
    data.data.cp_data["cp0"].data.get.charge_state = set_charge_state
    data.data.cp_data["cp0"].data.get.plug_state = plug_state
    data.data.cp_data["cp0"].plug_state_prev = plug_state_prev

    # execution
    charge_state, plugged_in = UpdateSoc()._get_ev_state(0)

    # evaluation
    assert charge_state == expected_charge_state
    assert plugged_in == expected_plugged_in


@pytest.mark.parametrize(
    "soc_module, force_soc_update, soc_interval_expired, ev_state, expected_threads_set",
    [
        pytest.param(None, False, False, (False, False), [], id="soc module none"),
        pytest.param(Mock(spec=Soc), False, True, (False, False), ["soc_ev0"], id="interval expired"),
        pytest.param(Mock(spec=Soc), True, False, (False, False), ["soc_ev0"], id="force soc update"),
        pytest.param(Mock(spec=Soc), False, False, (False, True), ["soc_ev0"], id="plugged in"),
        pytest.param(Mock(spec=Soc), False, False, (False, False), [], id="no soc request needed"),
    ]
)
def test_get_threads(soc_module: Optional[Soc],
                     force_soc_update: bool,
                     soc_interval_expired: bool,
                     ev_state: Tuple[bool, bool],
                     expected_threads_set: List[str],
                     monkeypatch):
    # setup
    ev = Ev(0)
    ev.soc_module = soc_module
    ev.data.get.force_soc_update = force_soc_update
    data.data.ev_data["ev0"] = ev
    soc_interval_expired_mock = Mock(return_value=soc_interval_expired)
    monkeypatch.setattr(EvTemplate, "soc_interval_expired", soc_interval_expired_mock)
    get_ev_state_mock = Mock(return_value=(ev_state))
    monkeypatch.setattr(UpdateSoc, "_get_ev_state", get_ev_state_mock)
    monkeypatch.setattr(UpdateSoc, "_reset_force_soc_update", Mock())

    # execution
    threads_set, threads_update = UpdateSoc()._get_threads()

    # evaluation
    if threads_set:
        assert threads_set[0].name == expected_threads_set[0]
    else:
        assert threads_set == expected_threads_set
