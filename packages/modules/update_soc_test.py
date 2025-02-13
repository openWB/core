from typing import List, Optional
from unittest.mock import Mock

import pytest

from control import data
from control.chargepoint.chargepoint import Chargepoint
from control.chargepoint.chargepoint_data import Get, Log, Set
from control.chargepoint.chargepoint_state_update import ChargepointStateUpdate
from control.ev.ev import Ev, EvData
from control.ev.ev_template import EvTemplate, EvTemplateData
from control.ev.ev import Get as EvGet
from control.ev.ev import Set as EvSet
from helpermodules.subdata import SubData
from modules.common.abstract_vehicle import GeneralVehicleConfig, VehicleUpdateData
from modules.common.configurable_vehicle import ConfigurableVehicle
from modules.vehicles.tesla.soc import create_vehicle
from modules.update_soc import UpdateSoc


@pytest.fixture(autouse=True)
def mock_data() -> None:
    data.data_init(Mock())

    SubData(*([Mock()]*18))
    SubData.cp_data = {"cp0":  Mock(spec=ChargepointStateUpdate, chargepoint=Mock(
        spec=Chargepoint,
        id=id,
        chargepoint_module=Mock(),
        data=Mock(
            get=Mock(spec=Get),
            set=Mock(spec=Set,
                     log=Mock(spec=Log),
                     charging_ev_data=Mock(spec=Ev,
                                           ev_template=Mock(spec=EvTemplate, data=Mock(spec=EvTemplateData)))))))}
    SubData.ev_data.update({"ev0": Mock(
        spec=Ev,
        num=0,
        data=Mock(spec=EvData, ev_template=0, get=Mock(spec=EvGet, fault_state=0),
                  set=Mock(spec=EvSet, soc_error_counter=0)),
        soc_module=Mock(spec=ConfigurableVehicle,
                        general_config=Mock(spec=GeneralVehicleConfig, use_soc_from_cp=False)))})
    SubData.ev_template_data.update({"et0": Mock(
        spec=EvTemplate, data=Mock(spec=EvTemplateData, battery_capacity=82000))})


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
    SubData.cp_data["cp0"].chargepoint.data.set.charging_ev = ev_num
    SubData.cp_data["cp0"].chargepoint.data.get.charge_state = set_charge_state

    # execution
    vehicle_update_data = UpdateSoc(Mock())._get_vehicle_update_data(0)

    # evaluation
    assert vehicle_update_data.charge_state == expected_charge_state


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
    SubData.ev_data["ev0"] = ev
    soc_interval_expired_mock = Mock(return_value=soc_interval_expired)
    monkeypatch.setattr(Ev, "soc_interval_expired", soc_interval_expired_mock)
    get_vehicle_update_data_mock = Mock(return_value=VehicleUpdateData())
    monkeypatch.setattr(UpdateSoc, "_get_vehicle_update_data", get_vehicle_update_data_mock)
    monkeypatch.setattr(UpdateSoc, "_reset_force_soc_update", Mock())

    # execution
    threads_update = UpdateSoc(Mock())._get_threads()[0]

    # evaluation
    if threads_update:
        assert threads_update[0].name == expected_threads_update[0]
    else:
        assert threads_update == expected_threads_update
