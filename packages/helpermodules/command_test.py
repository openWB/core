from unittest.mock import Mock

import pytest

from control.chargepoint.chargepoint import Chargepoint
from control.chargepoint.chargepoint_state_update import ChargepointStateUpdate
import dataclass_utils
from helpermodules.command import Command
from helpermodules.subdata import SubData
from modules.chargepoints.external_openwb.config import OpenWBSeries
from modules.chargepoints.internal_openwb.config import (InternalOpenWB, InternalOpenWBConfiguration,
                                                         InternalChargepointMode)
from modules.chargepoints.openwb_pro.chargepoint_module import ChargepointModule as ChargepointModulePro
from modules.chargepoints.internal_openwb.chargepoint_module import ChargepointModule as ChargepointModuleInternal


@pytest.fixture
def subdata_fixture() -> None:
    SubData(*([Mock()]*18))
    SubData.cp_data = {"cp0":  Mock(spec=ChargepointStateUpdate, chargepoint=Mock(
        spec=Chargepoint, chargepoint_module=Mock(spec=ChargepointModulePro)))}


@pytest.mark.parametrize(
    "additional_cp_mode, config, expected_msg",
    [
        pytest.param(None, OpenWBSeries(), None, id="Series hinzufügen"),
        pytest.param(None, InternalOpenWB(), None, id="Erste Duo hinzufügen"),
        pytest.param(InternalChargepointMode.DUO.value,
                     InternalOpenWB(),
                     None, id="Zweite Duo hinzufügen"),
        pytest.param(None, InternalOpenWB(),
                     None, id="Series hinzufügen"),
        pytest.param(InternalChargepointMode.SERIES.value,
                     InternalOpenWB(), Command.MAX_NUM_REACHED,
                     id="Zweite Series hinzufügen"),
    ]
)
def test_check_max_num_of_internal_chargepoints(additional_cp_mode, config, expected_msg, subdata_fixture, monkeypatch):
    # setup
    monkeypatch.setattr(Command, "_get_max_ids", Mock())
    monkeypatch.setattr(Command, "_get_max_id_by_json_object", Mock())
    if additional_cp_mode:
        SubData.cp_data.update(
            {"cp1": Mock(spec=ChargepointStateUpdate, chargepoint=Mock(
                spec=Chargepoint, chargepoint_module=Mock(spec=ChargepointModuleInternal, config=InternalOpenWB(
                    configuration=InternalOpenWBConfiguration(mode=additional_cp_mode)))))})

    # execution
    msg = Command(Mock())._check_max_num_of_internal_chargepoints(dataclass_utils.asdict(config))

    # evaluation
    assert msg == expected_msg
