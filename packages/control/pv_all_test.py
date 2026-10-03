from unittest.mock import Mock

from control import data
from control.limiting_value import loadmanagement_limit_factory
from control.pv import Pv
from control.pv_all import PvAll
from modules.common.fault_state_level import FaultStateLevel


def _setup_io_actions():
    data.data.io_actions = Mock(stepwise_control=Mock(return_value=(None, loadmanagement_limit_factory())))


def test_calc_power_for_all_components_counts_healthy_module(data_):
    # setup
    data.data.pv_data = {"pv1": Pv(1)}
    data.data.pv_data["pv1"].data.get.power = -500
    _setup_io_actions()
    pv_all = PvAll()

    # execution
    pv_all.calc_power_for_all_components()

    # evaluation
    assert pv_all.data.get.power == -500


def test_calc_power_for_all_components_trusts_already_zeroed_module(data_):
    # setup
    # pv2 ist seit über 60s im Fehlerzustand, power schon vom Modul genullt - PvAll summiert nur noch.
    data.data.pv_data = {"pv1": Pv(1), "pv2": Pv(2)}
    data.data.pv_data["pv1"].data.get.power = -500
    data.data.pv_data["pv2"].data.get.power = 0
    data.data.pv_data["pv2"].data.get.fault_state = FaultStateLevel.ERROR
    _setup_io_actions()
    pv_all = PvAll()

    # execution
    pv_all.calc_power_for_all_components()

    # evaluation
    assert pv_all.data.get.power == -500
