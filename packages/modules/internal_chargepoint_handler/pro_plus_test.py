import re
from threading import Event, Thread
from types import SimpleNamespace
from typing import Callable, Tuple
from unittest.mock import Mock

import pytest
import requests
from modules.internal_chargepoint_handler.pro_plus import SubData
from modules.common.component_state import ChargepointState
from modules.common import req
from modules.common.store._chargepoint_internal import get_internal_chargepoint_value_store
from modules.internal_chargepoint_handler.internal_chargepoint_handler import InternalChargepointHandler, UpdateState
from modules.internal_chargepoint_handler import internal_chargepoint_handler as handler_module
from modules.chargepoints.internal_openwb.config import InternalChargepointMode
from modules.internal_chargepoint_handler.internal_chargepoint_handler_config import (
    GlobalHandlerData, InternalChargepoint, InternalChargepointData, RfidData)
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
    monkeypatch.setattr(pro_plus.store_internal, "set", mock_store_set)
    monkeypatch.setattr(pro_plus.store_internal, "update", lambda: None)
    return pro_plus, mock_store_set


@pytest.mark.parametrize("secondary", [False, True])
@pytest.mark.parametrize("read_error", [False, True])
def test_get_values_publishes_local_status_only_on_secondary(
        setup_pro_plus, monkeypatch, mock_pub, secondary, read_error):
    pro_plus = setup_pro_plus[0]
    pro_plus.store_internal = get_internal_chargepoint_value_store(0)
    monkeypatch.setattr(SubData, "general_data", SimpleNamespace(data=SimpleNamespace(extern=secondary)))
    monkeypatch.setattr(handler_module, "ProPlus", Mock(return_value=pro_plus))
    handler_module.HandlerChargepoint(
        None, 0, InternalChargepointMode.PRO_PLUS,
        GlobalHandlerData(parent_ip="primary" if secondary else "localhost"), InternalChargepoint(), 1)
    states = [
        ChargepointState(power=6900, imported=1000, exported=0, currents=[30, 0, 0],
                         phases_in_use=1, charge_state=True, plug_state=True),
        ChargepointState(power=0, imported=1001, exported=0, currents=[0, 0, 0],
                         phases_in_use=1, charge_state=False, plug_state=True),
    ]
    monkeypatch.setattr(pro_plus, "request_values", Mock(side_effect=[
        states[0], requests.exceptions.ConnectTimeout() if read_error else states[1]]))
    monkeypatch.setattr(pro_plus.client_error_context, "error_counter_exceeded", Mock(return_value=read_error))
    mock_pub.pub.reset_mock()

    # Ein abrupter Ladestopp muss auf der Secondary sichtbar sein, darf aber auf der
    # Primary den zusammen mit virtuellen Zählern publizierten Datenstand nicht überschreiben.
    assert pro_plus.get_values(False, None) is states[0]
    if read_error:
        with pytest.raises(Exception, match=re.escape(ProPlus.NO_CONNECTION_TO_INTERNAL_CP)):
            pro_plus.get_values(False, None)
    else:
        assert pro_plus.get_values(False, None) is states[1]

    assert [call.args[1] for call in mock_pub.pub.call_args_list
            if call.args[0] == "openWB/set/internal_chargepoint/0/get/power"] == [6900, 0]
    status_calls = [call for call in mock_pub.pub.call_args_list
                    if call.args[0].startswith("openWB/set/chargepoint/")]
    if secondary:
        assert [call.args[1] for call in status_calls
                if call.args[0] == "openWB/set/chargepoint/1/get/power"] == [6900, 0]
        for field in ("currents", "charge_state", "plug_state", "phases_in_use", "imported", "version"):
            assert any(call.args[0] == f"openWB/set/chargepoint/1/get/{field}" for call in status_calls)
    else:
        assert status_calls == []


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


@pytest.mark.parametrize("read_error", [False, True])
def test_handler_updates_publication_targets_after_role_change(setup_pro_plus, monkeypatch, mock_pub, read_error):
    pro_plus = setup_pro_plus[0]
    pro_plus.store_internal = get_internal_chargepoint_value_store(0)
    general_data = SimpleNamespace(data=SimpleNamespace(extern=False))
    monkeypatch.setattr(SubData, "general_data", general_data)
    monkeypatch.setattr(handler_module, "ProPlus", Mock(return_value=pro_plus))
    status_store_factory = Mock(wraps=handler_module.get_chargepoint_value_store)
    monkeypatch.setattr(handler_module, "get_chargepoint_value_store", status_store_factory)
    handler = handler_module.HandlerChargepoint(
        None, 0, InternalChargepointMode.PRO_PLUS, GlobalHandlerData(parent_ip="localhost"), InternalChargepoint(), 1)
    handler.update_state = Mock(
        handle_unlock=Mock(return_value=False), cp_interruption_thread=None, phase_switch_thread=None)
    monkeypatch.setattr(handler, "_check_heartbeat_expired", Mock(return_value=False))
    state = ChargepointState(
        power=6900, imported=1000, exported=0, currents=[30, 0, 0],
        phases_in_use=1, charge_state=True, plug_state=True)
    pro_plus.old_chargepoint_state = state
    monkeypatch.setattr(pro_plus, "request_values", Mock(
        return_value=state, side_effect=requests.exceptions.ConnectTimeout() if read_error else None))
    monkeypatch.setattr(pro_plus.client_error_context, "error_counter_exceeded", Mock(return_value=read_error))

    # Derselbe Handler muss Wechsel in beide Richtungen vor der nächsten Abfrage übernehmen,
    # auch wenn die Abfrage Ersatzwerte publiziert und anschließend eine Exception auslöst.
    for secondary in (False, True, False, True):
        general_data.data.extern = secondary
        mock_pub.pub.reset_mock()
        assert handler.update(GlobalHandlerData(), InternalChargepointData(), RfidData()) is not read_error
        mock_pub.pub.assert_any_call("openWB/set/internal_chargepoint/0/get/power", 0 if read_error else 6900)
        status_power = [call.args[1] for call in mock_pub.pub.call_args_list
                        if call.args[0] == "openWB/set/chargepoint/1/get/power"]
        assert status_power == ([0 if read_error else 6900] if secondary else [])

    status_store_factory.assert_called_once_with(1)


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


@pytest.mark.parametrize("request_error", [None, requests.exceptions.ReadTimeout("Keine Antwort")])
def test_cp_interruption_blocks_commands_until_timer_expires(setup_pro_plus, pro_session, monkeypatch, request_error):
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
    pro_session.post.side_effect = [Mock(), request_error if request_error else Mock()]

    try:
        update_state.update_state(command, False)
        assert timer_started.wait(5)
        pro_session.post.assert_any_call(
            "http://192.168.192.50/connect.php",
            data={"cp_interrupt": True, "cp_interrupt_version": "0V", "cp_interrupt_duration": 30})
        assert pro_session.post.call_count == 2  # Stromvorgabe und CP-Auftrag
        if request_error:
            assert pro_plus.fault_state.fault_state != 0
            assert "Timeout" in pro_plus.fault_state.fault_str
        pro_session.post.reset_mock()
        pro_session.post.side_effect = None

        command.cp_interruption_duration = 0
        command.set_current = 16
        command.trigger_phase_switch = True
        update_state.update_state(command, False)

        assert update_state.cp_interruption_thread.is_alive()
        pro_session.post.assert_not_called()
        phase_switch.assert_not_called()

        update_state.update_state(command, True)
        pro_session.post.assert_called_once_with("http://192.168.192.50/connect.php", data={"ampere": 0})
        phase_switch.assert_not_called()
        assert update_state.cp_interruption_thread.is_alive()
        pro_session.post.reset_mock()
        update_state.update_state(command, False)
        pro_session.post.assert_not_called()
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
    phase_started = Event()
    phase_finished = Event()

    def switch_phases(phases):
        assert phases == 3
        phase_started.set()
        assert phase_finished.wait(5)

    monkeypatch.setattr(pro_plus, "perform_phase_switch", switch_phases)
    cp_interruption = Mock()
    monkeypatch.setattr(pro_plus, "perform_cp_interruption", cp_interruption)
    update_state = UpdateState(pro_plus, 1)
    command = InternalChargepointData(trigger_phase_switch=True, phases_to_use=3, cp_interruption_duration=30)

    try:
        update_state.update_state(command, False)
        assert phase_started.wait(5)
        cp_interruption.assert_not_called()
        assert update_state.cp_interruption_thread is None
        command.trigger_phase_switch = False
        update_state.update_state(command, False)
        cp_interruption.assert_not_called()
    finally:
        phase_finished.set()
        update_state.phase_switch_thread.join(5)

    update_state.update_state(command, False)
    update_state.cp_interruption_thread.join(5)
    cp_interruption.assert_called_once_with(30)


@pytest.mark.parametrize("loop_error", [False, True])
def test_handler_waits_for_cp_interruption_before_returning(setup_pro_plus, monkeypatch, loop_error):
    pro_plus = setup_pro_plus[0]
    timer_started = Event()
    timer_expired = Event()
    joining = Event()
    returned = Event()

    def wait_for_timer(duration):
        timer_started.set()
        assert timer_expired.wait(5)

    monkeypatch.setattr("modules.internal_chargepoint_handler.pro_plus.time.sleep", wait_for_timer)
    state = UpdateState(pro_plus, 1)
    state.update_state(InternalChargepointData(set_current=6, cp_interruption_duration=30), False)
    assert timer_started.wait(5)
    real_join = state.cp_interruption_thread.join

    def join():
        joining.set()
        real_join()

    monkeypatch.setattr(state.cp_interruption_thread, "join", join)
    runner = object.__new__(InternalChargepointHandler)
    runner.cp0 = SimpleNamespace(mode=InternalChargepointMode.PRO_PLUS, update_state=state)
    runner.cp1 = None
    runner.event_stop = Mock(is_set=Mock(side_effect=RuntimeError("Loop fehlgeschlagen"))) if loop_error else Event()
    if not loop_error:
        runner.event_stop.set()
    runner.fault_state_info_cp0 = pro_plus.fault_state

    def stop_handler():
        runner.loop()
        returned.set()

    worker = Thread(target=stop_handler)
    try:
        worker.start()
        assert joining.wait(5)
        assert not returned.is_set()
        assert state.cp_interruption_thread.is_alive()
    finally:
        timer_expired.set()
        worker.join(5)
        real_join(5)
    assert returned.is_set()
    assert not worker.is_alive()
    assert not state.cp_interruption_thread.is_alive()
