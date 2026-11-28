from typing import List, Optional
from unittest.mock import MagicMock

import pytest

from modules.internal_chargepoint_handler import chargepoint_module
from modules.internal_chargepoint_handler.chargepoint_module import ChargepointModule


@pytest.mark.parametrize(
    "currents, evse_state, expected",
    [
        pytest.param([0.0, 0.0, 0.0], 2, True, id="0 A, State B"),
        pytest.param([0.0, 0.0, 0.0], 1, True, id="0 A, State A (abgesteckt)"),
        pytest.param([0.0, 0.857, 0.013], 2, False, id="Restlast auf L2 bei State B"),
        pytest.param([15.6, 9.7, 15.9], 3, False, id="Last, State C"),
        pytest.param([0.0, 0.0, 0.0], 3, False, id="0 A, aber noch State C"),
        pytest.param([0.0, 0.0, 0.0], 4, False, id="0 A, State D"),
        pytest.param([0.0, 0.0, 0.0], 5, False, id="EVSE-Fehler"),
        pytest.param([None, None, None], 2, False, id="keine Messwerte (B23 NaN)"),
        pytest.param([0.0, None, 0.0], 2, False, id="eine Phase ohne Messwert"),
        pytest.param([-0.2, 0.0, 0.0], 2, True, id="Rauschen negativ"),
        pytest.param([-3.0, 0.0, 0.0], 2, False, id="Strom negativ (Zähler verdreht)"),
        pytest.param(None, 2, True, id="kein Zähler, State B"),
        pytest.param(None, 3, False, id="kein Zähler, State C"),
    ])
def test_vehicle_stopped_charging(currents: Optional[List[Optional[float]]], evse_state: int, expected: bool):
    assert ChargepointModule._vehicle_stopped_charging(currents, evse_state) == expected


@pytest.fixture
def module(monkeypatch) -> ChargepointModule:
    monkeypatch.setattr("time.sleep", lambda seconds: None)
    monkeypatch.setattr(chargepoint_module, "GPIO", MagicMock(), raising=False)
    cp = ChargepointModule.__new__(ChargepointModule)
    cp.local_charge_point_num = 0
    cp.old_phases_in_use = 3
    cp.fault_state = MagicMock()
    cp.fault_state.component_info.name = "Interner Ladepunkt 0"
    cp._client = MagicMock()
    cp._client.get_pins_phase_switch.return_value = (7, 11)
    return cp


def counter_state(currents):
    state = MagicMock()
    state.currents = currents
    return state


def test_perform_phase_switch_waits_for_meter_and_evse(module: ChargepointModule):
    module._client.evse_client.get_state_number.side_effect = [3, 2, 2]
    module._client.meter_client.get_counter_state.side_effect = [
        counter_state([15.6, 9.7, 15.9]), counter_state([0.0, 0.857, 0.013]), counter_state([0.0, 0.0, 0.0])]

    module.perform_phase_switch(1)

    assert module._client.evse_client.get_state_number.call_count == 3
    assert module._client.evse_client.set_current.call_count == 3  # einmal vorab, je Wartedurchlauf erneut
    assert chargepoint_module.GPIO.output.call_count == 4
    assert module.old_phases_in_use == 1


def test_perform_phase_switch_continues_after_read_error(module: ChargepointModule):
    module._client.evse_client.get_state_number.side_effect = [Exception("No response received"), 2]
    module._client.meter_client.get_counter_state.return_value = counter_state([0.0, 0.0, 0.0])

    module.perform_phase_switch(1)

    assert chargepoint_module.GPIO.output.call_count == 4
    assert module.old_phases_in_use == 1


def test_perform_phase_switch_aborts_without_confirmation(module: ChargepointModule, monkeypatch):
    monkeypatch.setattr(ChargepointModule, "PHASE_SWITCH_METER_POLLS", 3)
    module._client.evse_client.get_state_number.return_value = 3
    module._client.meter_client.get_counter_state.return_value = counter_state([15.6, 9.7, 15.9])

    with pytest.raises(Exception, match="Phasenumschaltung abgebrochen"):
        module.perform_phase_switch(1)

    assert module._client.evse_client.get_state_number.call_count == 3
    chargepoint_module.GPIO.output.assert_not_called()
    assert module.old_phases_in_use == 3


def test_perform_phase_switch_without_meter_uses_evse_state(module: ChargepointModule):
    module._client.meter_client = None
    module._client.evse_client.get_state_number.side_effect = [3, 2]

    module.perform_phase_switch(1)

    assert chargepoint_module.GPIO.output.call_count == 4
    assert module.old_phases_in_use == 1


def test_perform_phase_switch_starts_recovery_window_even_if_relay_fails(module: ChargepointModule,
                                                                         monkeypatch):
    monkeypatch.setattr("time.monotonic", lambda: 100.0)
    module._client.evse_client.get_state_number.return_value = 2
    module._client.meter_client.get_counter_state.return_value = counter_state([0.0, 0.0, 0.0])
    module.cp_active_timestamp = None
    chargepoint_module.GPIO.output.side_effect = [None, RuntimeError("Relais"), None]

    with pytest.raises(RuntimeError):
        module.perform_phase_switch(1)

    assert module.cp_active_timestamp == 100.0


@pytest.fixture
def value_module(module: ChargepointModule, monkeypatch) -> ChargepointModule:
    module.old_plug_state = True
    module.cp_active_timestamp = None
    module.old_chargepoint_state = MagicMock()
    module.store_internal = MagicMock()
    module.client_error_context = MagicMock()
    module.client_error_context.error_counter_exceeded.return_value = False
    module.version = module.current_branch = module.current_commit = ""
    module.PLUG_STANDBY_POWER_THRESHOLD = 10
    return module


def _read(module: ChargepointModule, plug_state: bool, cp_active: bool = False) -> bool:
    evse_state = MagicMock(plug_state=plug_state, charge_state=False, set_current=0, max_current=16)
    counter = MagicMock(power=0, currents=[0.0, 0.0, 0.0], imported=0, powers=[0.0] * 3, voltages=[230.0] * 3,
                        frequency=50, power_factors=[0.0] * 3, serial_number="1")
    module._client.request_and_check_hardware.return_value = (evse_state, counter)
    return module.get_values(cp_active, None).plug_state


def test_plug_state_kept_until_vehicle_reports_state_b_after_cp_interruption(value_module: ChargepointModule,
                                                                             monkeypatch):
    now = [100.0]
    monkeypatch.setattr("time.monotonic", lambda: now[0])

    assert _read(value_module, plug_state=False, cp_active=True) is True
    value_module.cp_active_timestamp = now[0]  # Thread beendet
    now[0] += 0.4
    assert _read(value_module, plug_state=False) is True  # State A direkt nach CP-Wiederkehr
    assert _read(value_module, plug_state=True) is True  # State B
    assert _read(value_module, plug_state=False) is False  # echtes Abstecken


def test_plug_state_kept_if_thread_finished_between_two_reads(value_module: ChargepointModule, monkeypatch):
    now = [100.0]
    monkeypatch.setattr("time.monotonic", lambda: now[0])

    value_module.perform_cp_interruption(1)  # kurze Unterbrechung, nie während get_values aktiv gesehen

    assert value_module.cp_active_timestamp == 100.0
    assert _read(value_module, plug_state=False) is True


def test_plug_state_false_after_recovery_timeout(value_module: ChargepointModule, monkeypatch):
    now = [100.0]
    monkeypatch.setattr("time.monotonic", lambda: now[0])

    value_module.cp_active_timestamp = now[0]
    now[0] += ChargepointModule.CP_RECOVERY_TIMEOUT + 0.1
    assert _read(value_module, plug_state=False) is False


def test_plug_state_false_without_preceding_cp_interruption(value_module: ChargepointModule):
    assert _read(value_module, plug_state=False) is False
