import re
from threading import Event
from typing import Callable, Tuple
from unittest.mock import Mock

import pytest
import requests
from modules.internal_chargepoint_handler.pro_plus import SubData
from modules.common.component_state import ChargepointState
from modules.common import req
from modules.internal_chargepoint_handler.internal_chargepoint_handler import UpdateState
from modules.internal_chargepoint_handler.internal_chargepoint_handler_config import (
    InternalChargepoint, InternalChargepointData)
from modules.internal_chargepoint_handler.pro_plus import ProPlus


@pytest.fixture()
def pro_session(monkeypatch) -> Mock:
    session = Mock()
    monkeypatch.setattr(req, "get_http_session", Mock(return_value=session))
    return session


@pytest.fixture(autouse=True)
def setup_pro_plus(monkeypatch, pro_session) -> Tuple[ProPlus, Mock]:
    system_data_mock = Mock(data={"version": "1.0.0", "current_branch": "main", "current_commit": "abc123"})
    monkeypatch.setattr(SubData, "system_data", {"system": system_data_mock})
    pro_plus = ProPlus(0, InternalChargepoint(), 1)
    mock_store_set = Mock()
    monkeypatch.setattr(pro_plus.store, "set", mock_store_set)
    monkeypatch.setattr(pro_plus.store, "update", lambda: None)
    monkeypatch.setattr(pro_plus.store_internal, "set", lambda x: None)
    monkeypatch.setattr(pro_plus.store_internal, "update", lambda: None)
    return pro_plus, mock_store_set


@pytest.fixture()
def chargepoint_state() -> ChargepointState:
    return ChargepointState(currents=[0, 0, 0], powers=[0, 0, 0], voltages=[
        229.4, 229.4, 229.4], imported=0, exported=0, power=0, phases_in_use=2, charge_state=False, plug_state=True)


@pytest.mark.parametrize(
    "request_values_return, expected_chargepoint_state",
    [pytest.param(lambda: chargepoint_state, chargepoint_state, id="Normalfall"),
     pytest.param(Mock(side_effect=Exception(ProPlus.NO_CONNECTION_TO_INTERNAL_CP)),
                  chargepoint_state, id="Fehler, aber Timer noch nicht abgelaufen")])
def test_get_values(request_values_return: ChargepointState,
                    expected_chargepoint_state: ChargepointState,
                    setup_pro_plus: Callable[[], Tuple[ProPlus, Mock]],
                    monkeypatch):
    # setup
    pro_plus, mock_store_set = setup_pro_plus
    pro_plus.old_chargepoint_state = expected_chargepoint_state
    monkeypatch.setattr(pro_plus, "request_values", request_values_return)
    monkeypatch.setattr(pro_plus.client_error_context, "error_counter_exceeded", lambda: False)

    # execution
    chargepoint_state = pro_plus.get_values(False, None)

    # evalutation
    assert chargepoint_state == expected_chargepoint_state
    assert mock_store_set.call_args.args[0].__dict__ == expected_chargepoint_state.__dict__


def test_get_values_no_data_since_boot(setup_pro_plus: Callable[[], Tuple[ProPlus, Mock]], monkeypatch):
    # setup
    pro_plus = setup_pro_plus[0]
    monkeypatch.setattr(pro_plus, "request_values", Mock(side_effect=Exception(ProPlus.NO_CONNECTION_TO_INTERNAL_CP)))
    monkeypatch.setattr(pro_plus.client_error_context, "error_counter_exceeded", lambda: False)

    # execution
    with pytest.raises(Exception, match=re.escape(ProPlus.NO_DATA_SINCE_BOOT)):
        pro_plus.get_values(False, None)


def test_get_values_error_timer_exceed(setup_pro_plus: Callable[[], Tuple[ProPlus, Mock]], monkeypatch):
    # Exception werfen und Ladepunkt-Status zurücksetzen
    # setup
    pro_plus, mock_store_set = setup_pro_plus
    pro_plus.old_chargepoint_state = ChargepointState(
        plug_state=False, charge_state=False, imported=None, exported=None,
        phases_in_use=0, power=0, currents=[0]*3)
    monkeypatch.setattr(pro_plus, "request_values", Mock(side_effect=requests.exceptions.ConnectTimeout()))
    monkeypatch.setattr(pro_plus.client_error_context, "error_counter_exceeded", lambda: True)

    # execution
    with pytest.raises(Exception, match=re.escape(ProPlus.NO_CONNECTION_TO_INTERNAL_CP)):
        pro_plus.get_values(False, None)

    assert mock_store_set.call_args.args[0].__dict__ == ChargepointState(
        plug_state=False, charge_state=False, imported=None, exported=None,
        phases_in_use=0, power=0, currents=[0]*3).__dict__


def test_cp_interruption_blocks_commands_until_timer_expires(setup_pro_plus, pro_session, monkeypatch):
    pro_plus = setup_pro_plus[0]
    timer_started = Event()
    timer_expired = Event()

    def wait_for_timer(duration):
        assert duration == 30
        timer_started.set()
        assert timer_expired.wait(5)

    monkeypatch.setattr("modules.internal_chargepoint_handler.pro_plus.time.sleep", wait_for_timer)
    phase_switch = Mock()
    monkeypatch.setattr(pro_plus, "perform_phase_switch", phase_switch)
    update_state = UpdateState(pro_plus, 1)
    command = InternalChargepointData(set_current=6, cp_interruption_duration=30)
    pro_session.post.reset_mock()

    try:
        update_state.update_state(command, False)
        assert timer_started.wait(5)
        pro_session.post.assert_any_call(
            "http://192.168.192.50/connect.php",
            data={"cp_interrupt": True, "cp_interrupt_version": "0V", "cp_interrupt_duration": 30})
        assert pro_session.post.call_count == 2  # Stromvorgabe und CP-Auftrag
        pro_session.post.reset_mock()

        command.cp_interruption_duration = 0
        command.set_current = 16
        command.trigger_phase_switch = True
        update_state.update_state(command, False)

        assert update_state.cp_interruption_thread.is_alive()
        pro_session.post.assert_not_called()
        phase_switch.assert_not_called()
    finally:
        timer_expired.set()
        if update_state.cp_interruption_thread:
            update_state.cp_interruption_thread.join(5)

    assert not update_state.cp_interruption_thread.is_alive()
    command.trigger_phase_switch = False
    update_state.update_state(command, False)
    pro_session.post.assert_called_once_with("http://192.168.192.50/connect.php", data={"ampere": 16})


def test_phase_switch_defers_simultaneous_cp_interruption(setup_pro_plus, monkeypatch):
    pro_plus = setup_pro_plus[0]
    monkeypatch.setattr(pro_plus, "set_current", Mock())
    monkeypatch.setattr(pro_plus, "perform_phase_switch", Mock())
    cp_interruption = Mock()
    monkeypatch.setattr(pro_plus, "perform_cp_interruption", cp_interruption)
    update_state = UpdateState(pro_plus, 1)
    command = InternalChargepointData(trigger_phase_switch=True, phases_to_use=3, cp_interruption_duration=30)

    update_state.update_state(command, False)
    update_state.phase_switch_thread.join(5)
    cp_interruption.assert_not_called()
    assert update_state.cp_interruption_thread is None

    command.trigger_phase_switch = False
    update_state.update_state(command, False)
    update_state.cp_interruption_thread.join(5)
    cp_interruption.assert_called_once_with(30)
