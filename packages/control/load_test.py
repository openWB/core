from typing import Dict
from unittest.mock import Mock

import pytest

from control import data, load
from control.chargepoint.chargepoint import Chargepoint
from control.chargepoint.chargepoint_state import ChargepointState
from control.consumer.consumer import Consumer


def _setup_control_data(cp_data: Dict[str, Chargepoint], consumer_data: Dict[str, Consumer]):
    data.data_init(Mock())
    data.data.cp_data = cp_data
    data.data.consumer_data = consumer_data

    evu_counter = Mock()
    evu_counter.reset_pv_data = Mock()
    data.data.counter_all_data = Mock(get_evu_counter=Mock(return_value=evu_counter))
    return evu_counter


def test_reset_pv_data_when_only_consumer_is_no_charging_allowed():
    consumer = Mock(spec=Consumer, num="1")
    consumer.data = Mock(control_parameter=Mock(state=ChargepointState.NO_CHARGING_ALLOWED))
    evu_counter = _setup_control_data({}, {"consumer1": consumer})

    load.reset_pv_data_if_no_active_delays()

    evu_counter.reset_pv_data.assert_called_once()


def test_do_not_reset_pv_data_when_consumer_switch_off_delay_active():
    consumer = Mock(spec=Consumer, num="1")
    consumer.data = Mock(control_parameter=Mock(state=ChargepointState.SWITCH_OFF_DELAY))
    evu_counter = _setup_control_data({}, {"consumer1": consumer})

    load.reset_pv_data_if_no_active_delays()

    evu_counter.reset_pv_data.assert_not_called()


def test_reset_pv_data_with_chargepoint_no_charging_allowed():
    # eine wartende, aber nicht (mehr) reservierte Komponente darf den robustness-Reset nicht dauerhaft
    # blockieren - jede Reservierung wird bereits beim Übergang in NO_CHARGING_ALLOWED freigegeben.
    cp = Mock(spec=Chargepoint, num="1")
    cp.data = Mock(control_parameter=Mock(state=ChargepointState.NO_CHARGING_ALLOWED))
    evu_counter = _setup_control_data({"cp1": cp}, {})

    load.reset_pv_data_if_no_active_delays()

    evu_counter.reset_pv_data.assert_called_once()


@pytest.mark.parametrize("state", [ChargepointState.PERFORMING_PHASE_SWITCH,
                                   ChargepointState.PHASE_SWITCH_DELAY,
                                   ChargepointState.SWITCH_OFF_DELAY,
                                   ChargepointState.SWITCH_ON_DELAY])
def test_do_not_reset_pv_data_with_chargepoint_holding_a_reservation(state):
    cp = Mock(spec=Chargepoint, num="1")
    cp.data = Mock(control_parameter=Mock(state=state))
    evu_counter = _setup_control_data({"cp1": cp}, {})

    load.reset_pv_data_if_no_active_delays()

    evu_counter.reset_pv_data.assert_not_called()
