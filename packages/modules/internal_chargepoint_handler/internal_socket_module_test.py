from unittest.mock import MagicMock, Mock

import pytest

from modules.common.component_state import CounterState, ConsumerState
from modules.common.store import _socket_internal
from modules.internal_chargepoint_handler import internal_socket


@pytest.mark.parametrize("tag", ["0012345678", None])
def test_internal_socket_measurement_publishes_current_rfid_and_clears_previous_tag(tag, monkeypatch):
    publisher = Mock()
    monkeypatch.setattr(_socket_internal, "pub_to_broker", publisher)
    monkeypatch.setattr(internal_socket.time, "sleep", Mock())
    module = internal_socket.InternalSocketModule.__new__(internal_socket.InternalSocketModule)
    module._client = Mock()
    module._client.request_and_check_socket.return_value = CounterState(
        power=100, imported=20, exported=0, currents=[1, 0, 0], voltages=[230, 0, 0])
    module.client_error_context = MagicMock()
    module.client_error_context.error_counter_exceeded.return_value = False
    module.fault_state = Mock()
    module.current_state = False
    module.measurement_valid = False
    module.old_socket_state = ConsumerState(power=0)
    module.store_internal = _socket_internal.InternalSocketValueStore()

    state = module.get_values(tag)

    assert isinstance(state, ConsumerState)
    assert state.rfid == tag
    assert state.power == 100
    publisher.assert_any_call("openWB/set/internal_socket/get/rfid", tag)
    publisher.reset_mock()

    state = module.get_values(None)

    assert state.rfid is None
    publisher.assert_any_call("openWB/set/internal_socket/get/rfid", None)
