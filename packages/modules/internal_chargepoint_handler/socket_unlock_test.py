from contextlib import nullcontext
import time
from threading import Event
from types import SimpleNamespace
from unittest.mock import MagicMock, Mock

import pytest

from modules.internal_chargepoint_handler import socket
from modules.internal_chargepoint_handler.socket import ActorState, Socket
from modules.internal_chargepoint_handler import internal_chargepoint_handler as handler
from modules.common import connector_unlock as unlock


@pytest.fixture(autouse=True)
def local_requests(monkeypatch):
    monkeypatch.setattr(unlock, "_requests", {})


@pytest.fixture
def hardware(monkeypatch):
    gpio = Mock()
    gpio.input.return_value = ActorState.CLOSED
    monkeypatch.setattr(socket, "GPIO", gpio, raising=False)
    clock = SimpleNamespace(now=100.0)
    monkeypatch.setattr(socket.time, "monotonic", lambda: clock.now)
    monkeypatch.setattr(socket.time, "sleep", lambda seconds: setattr(clock, "now", clock.now + seconds))
    cp = object.__new__(Socket)
    cp.local_charge_point_num = 0
    cp.fault_state = Mock()
    cp._unlock_blocked = False
    evse = SimpleNamespace(charge_state=False, set_current=0, plug_state=True)
    meter = SimpleNamespace(currents=[0.0, 0.0, 0.0])
    controller = Mock(id=1)
    controller.client.read_holding_registers.return_value = [0, 0, 2]
    cp._client = SimpleNamespace(client=MagicMock(), evse_client=controller,
                                 request_and_check_hardware=Mock(return_value=(evse, meter)))
    cp._Socket__open_actor = Mock(side_effect=lambda: setattr(gpio.input, "return_value", ActorState.OPENED))
    return cp, evse, meter, clock, gpio


def test_unlock_requires_stable_fresh_measurements_and_open_feedback(hardware):
    cp, _, _, clock, _ = hardware
    assert cp.perform_unlock(timeout=3)
    assert clock.now >= 102
    assert cp._client.request_and_check_hardware.call_count >= 3
    cp._Socket__open_actor.assert_called_once()
    assert cp.unlock_blocked


@pytest.mark.parametrize("currents", [[0, 0, 0.3], [-1, 0, 0], [0, float("nan"), 0],
                                      [0, float("inf"), 0], [0, None, 0], [0, 0], None])
def test_current_on_any_phase_or_invalid_measurement_never_opens(hardware, currents):
    cp, _, meter, _, _ = hardware
    meter.currents = currents
    assert not cp.perform_unlock(timeout=3)
    cp._Socket__open_actor.assert_not_called()
    assert cp.unlock_blocked


def test_zero_cached_fallback_does_not_authorize_unlock(hardware):
    cp, _, _, _, _ = hardware
    cp.chargepoint_state = SimpleNamespace(currents=[0, 0, 0], charge_state=False)
    cp._client.request_and_check_hardware.side_effect = OSError("meter unavailable")
    with pytest.raises(OSError):
        cp.perform_unlock(timeout=3)
    cp._Socket__open_actor.assert_not_called()
    assert cp.unlock_blocked


@pytest.mark.parametrize("raw_current,state", [(0, 3), (0, 4), (0, 5), (6, 2), (0, 999)])
def test_zero_measured_current_without_evse_shutdown_is_insufficient(hardware, raw_current, state):
    cp, _, _, _, _ = hardware
    cp._client.evse_client.client.read_holding_registers.return_value = [raw_current, 0, state]
    assert not cp.perform_unlock(timeout=3)
    cp._Socket__open_actor.assert_not_called()


def test_nonzero_current_resets_stability_window(hardware):
    cp, _, meter, clock, _ = hardware

    def values(_):
        meter.currents = [1, 0, 0] if clock.now == 101 else [0, 0, 0]
        return hardware[1], meter
    cp._client.request_and_check_hardware.side_effect = values
    assert not cp.perform_unlock(timeout=3)
    cp._Socket__open_actor.assert_not_called()


def test_read_finishing_after_deadline_cannot_open_actor(hardware, monkeypatch):
    cp, _, _, clock, _ = hardware

    def slow_read():
        clock.now += 4
        return True, True
    monkeypatch.setattr(cp, "_read_unlock_state", slow_read)
    assert not cp.perform_unlock(timeout=3)
    cp._Socket__open_actor.assert_not_called()


def test_actuator_command_without_open_feedback_is_failure(hardware):
    cp, _, _, _, _ = hardware
    cp._Socket__open_actor.side_effect = None
    assert not cp.perform_unlock(timeout=3)
    assert cp.unlock_blocked


def test_feedback_gpio_failure_cannot_prevent_zero_setpoint(hardware, monkeypatch):
    cp, _, _, _, gpio = hardware
    gpio.input.side_effect = OSError("feedback unavailable")
    with pytest.raises(OSError):
        cp.perform_unlock(timeout=3)
    cp._client.evse_client.set_current.assert_called_with(0)
    set_current = Mock()
    monkeypatch.setattr(socket.ChargepointModule, "set_current", set_current)
    cp.set_current(32)
    set_current.assert_called_once_with(0)
    cp._Socket__open_actor.assert_not_called()


def test_evse_stop_failure_never_opens_actor(hardware):
    cp, _, _, _, _ = hardware
    cp._client.evse_client.set_current.side_effect = OSError("EVSE unavailable")
    with pytest.raises(OSError):
        cp.perform_unlock(timeout=3)
    cp._Socket__open_actor.assert_not_called()
    assert cp.unlock_blocked


def test_no_relock_and_only_safe_disconnect_releases_charging_block(hardware, monkeypatch):
    cp, evse, _, _, _ = hardware
    assert cp.perform_unlock(timeout=3)
    cp.client_error_context = nullcontext()
    cp.socket_max_current = 32
    cp.chargepoint_state = SimpleNamespace(plug_state=True)
    monkeypatch.setattr(socket.ChargepointModule, "get_values", Mock(return_value=cp.chargepoint_state))
    cp._Socket__close_actor = Mock()
    cp.get_values(False, "")
    cp._Socket__close_actor.assert_not_called()
    assert cp.unlock_blocked
    evse.plug_state = False
    cp._client.evse_client.client.read_holding_registers.return_value = [0, 0, 3]
    cp.get_values(False, "")
    assert cp.unlock_blocked
    cp._client.evse_client.client.read_holding_registers.return_value = [0, 0, 2]
    cp.get_values(False, "")
    assert not cp.unlock_blocked


@pytest.mark.parametrize("busy,expected", [(False, "unlocked"), (True, "failed")])
def test_handler_owns_request_and_result_and_excludes_phase_switch(hardware, monkeypatch, mock_pub, busy, expected):
    cp = hardware[0]
    cp.perform_unlock = Mock(return_value=True)
    worker = handler.UpdateState(cp, 1)
    worker.phase_switch_thread = Mock(is_alive=Mock(return_value=busy))
    monkeypatch.setattr(handler, "SingleComponentUpdateContext", lambda *args, **kwargs: nullcontext())
    request = unlock.UnlockRequest(time.monotonic() + 20)
    unlock._requests[0] = request
    data = handler.InternalChargepointData()
    worker.update_state(data, False)
    if worker.unlock_thread:
        worker.unlock_thread.join(timeout=2)
        assert not worker.unlock_thread.is_alive()
    assert request.result.result() == expected
    assert not worker.handle_unlock()
    assert cp.perform_unlock.call_count == (0 if busy else 1)


def test_unlock_thread_is_nonblocking_and_excludes_normal_hardware_access(hardware, monkeypatch):
    cp = hardware[0]
    started, finish = Event(), Event()

    def perform_unlock(timeout, cancelled):
        started.set()
        assert finish.wait(2)
        return True

    cp.perform_unlock = Mock(side_effect=perform_unlock)
    cp.get_values = Mock()
    cp.set_current = Mock()
    state = handler.UpdateState(cp, 1)
    worker = object.__new__(handler.HandlerChargepoint)
    worker.module = cp
    worker.update_state = state
    worker.local_charge_point_num = 0
    monkeypatch.setattr(handler, "SingleComponentUpdateContext", lambda *args, **kwargs: nullcontext())
    request = unlock.UnlockRequest(time.monotonic() + 20)
    unlock._requests[0] = request
    data = handler.InternalChargepointData()
    state.update_state(data, False)
    try:
        assert started.wait(2)
        assert state.unlock_thread.is_alive()
        assert worker.update(SimpleNamespace(), data, SimpleNamespace())
        state.update_state(handler.InternalChargepointData(
            set_current=16, trigger_phase_switch=True, cp_interruption_duration=5), False)
        cp.get_values.assert_not_called()
        cp.set_current.assert_not_called()
        assert state.phase_switch_thread is None
        assert state.cp_interruption_thread is None
    finally:
        finish.set()
        state.unlock_thread.join(timeout=2)
    assert request.result.result() == "unlocked"


def test_unlock_worker_returns_failure_on_hardware_exception(hardware, monkeypatch):
    cp = hardware[0]
    cp.perform_unlock = Mock(side_effect=OSError("hardware unavailable"))
    state = handler.UpdateState(cp, 1)
    monkeypatch.setattr(handler, "SingleComponentUpdateContext", lambda *args, **kwargs: nullcontext())
    request = unlock.UnlockRequest(time.monotonic() + 20)
    unlock._requests[0] = request
    state.update_state(handler.InternalChargepointData(), False)
    state.unlock_thread.join(timeout=2)
    assert request.result.result() == "failed"


def test_loop_skips_shared_bus_chargepoint_and_joins_unlock_before_shutdown(monkeypatch):
    runner = object.__new__(handler.InternalChargepointHandler)
    state = SimpleNamespace(unlock_thread=None)
    thread = Mock(is_alive=Mock(return_value=True))
    runner.cp0 = SimpleNamespace(
        mode=handler.InternalChargepointMode.PRO_PLUS, update_state=state,
        update=Mock(side_effect=lambda *args: setattr(state, "unlock_thread", thread)))
    runner.cp1 = SimpleNamespace(update=Mock(), update_state=SimpleNamespace(unlock_thread=None))
    runner.event_stop = Mock(is_set=Mock(side_effect=[False, True]))
    runner.fault_state_info_cp0 = Mock()
    monkeypatch.setattr(handler, "SingleComponentUpdateContext", lambda *args, **kwargs: nullcontext())
    monkeypatch.setattr(handler, "clear_in_memory_log_handler", Mock())
    monkeypatch.setattr(handler.SubData, "system_data", {"system": SimpleNamespace(data={"debug_level": 10})})
    monkeypatch.setattr(handler.SubData, "internal_chargepoint_data", {
        "global_data": None, "cp0": SimpleNamespace(data=None), "rfid_data": None})
    runner.loop()
    runner.cp1.update.assert_not_called()
    thread.join.assert_called_once()


def test_cancellation_during_hardware_read_never_opens_actor(hardware, monkeypatch):
    cp = hardware[0]
    cancelled = Event()

    def read():
        cancelled.set()
        return True, True
    monkeypatch.setattr(cp, "_read_unlock_state", read)
    assert not cp.perform_unlock(timeout=3, cancelled=cancelled)
    cp._Socket__open_actor.assert_not_called()
    assert cp.unlock_blocked
