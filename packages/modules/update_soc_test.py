from typing import List, Optional
from unittest.mock import Mock

import pytest

from control import data
from control.chargepoint.chargepoint import Chargepoint, Get, Log, Set
from control.ev import Ev, EvTemplate, EvTemplateData
from modules.common.abstract_soc import SocUpdateData
from modules.vehicles.tesla.soc import create_vehicle
from modules.update_soc import UpdateSoc


@pytest.fixture(autouse=True)
def mock_data() -> None:
    data.data_init(Mock())
    data.data.cp_data["cp0"] = Mock(
        spec=Chargepoint,
        id=id,
        chargepoint_module=Mock(),
        data=Mock(
            get=Mock(spec=Get),
            set=Mock(spec=Set,
                     log=Mock(spec=Log),
                     charging_ev_data=Mock(spec=Ev,
                                           ev_template=Mock(spec=EvTemplate, data=Mock(spec=EvTemplateData))))))
    data.data.ev_data["ev0"] = Mock(
        spec=Ev,
        ev_template=Mock(
            spec=EvTemplate, data=Mock(spec=EvTemplateData, battery_capacity=82000)))


@pytest.mark.parametrize(
    "ev_num, set_charge_state, expected_charge_state",
    [
        pytest.param(1, False, False, id="ev not matched to cp"),
        pytest.param(0, False, False, id="ev not charging"),
        pytest.param(0, True, True, id="ev charging"),
    ])
def test_get_ev_state(ev_num: int,
                      set_charge_state: bool,
                      expected_charge_state: bool):
    # setup
    data.data.cp_data["cp0"].data.set.charging_ev = ev_num
    data.data.cp_data["cp0"].data.get.charge_state = set_charge_state

    # execution
    soc_update_data = UpdateSoc()._get_soc_update_data(0)

    # evaluation
    assert soc_update_data.charge_state == expected_charge_state


@pytest.mark.parametrize(
    "soc_module, force_soc_update, soc_interval_expired, expected_threads_update",
    [
        pytest.param(None, False, False, [], id="soc module none"),
        pytest.param(Mock(spec=create_vehicle, update=Mock()), False, True, ["fetch soc_ev0"], id="interval expired"),
        pytest.param(Mock(spec=create_vehicle, update=Mock()), True, False, ["fetch soc_ev0"], id="force soc update"),
        pytest.param(Mock(spec=create_vehicle, update=Mock()), False, False, [], id="no soc request needed"),
    ]
)
def test_get_threads(soc_module: Optional[create_vehicle],
                     force_soc_update: bool,
                     soc_interval_expired: bool,
                     expected_threads_update: List[str],
                     monkeypatch):
    # setup
    ev = Ev(0)
    ev.soc_module = soc_module
    ev.data.get.force_soc_update = force_soc_update
    data.data.ev_data["ev0"] = ev
    soc_interval_expired_mock = Mock(return_value=soc_interval_expired)
    monkeypatch.setattr(Ev, "soc_interval_expired", soc_interval_expired_mock)
    get_soc_update_data_mock = Mock(return_value=SocUpdateData())
    monkeypatch.setattr(UpdateSoc, "_get_soc_update_data", get_soc_update_data_mock)
    monkeypatch.setattr(UpdateSoc, "_reset_force_soc_update", Mock())

    # execution
    threads_update = UpdateSoc()._get_threads()[0]

    # evaluation
    if threads_update:
        assert threads_update[0].name == expected_threads_update[0]
    else:
        assert threads_update == expected_threads_update
