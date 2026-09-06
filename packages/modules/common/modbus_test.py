import threading
import time
from unittest.mock import Mock

from modules.common.modbus import ModbusClient, ModbusDataType


def _fake_response():
    response = Mock()
    response.isError.return_value = False
    response.registers = [0]
    return response


def test_concurrent_reads_and_writes_are_serialized_and_none_dropped():
    # Simulates the real-world case (internal_chargepoint_handler): the main poll loop reading the
    # EVSE state concurrently with a phase-switch/cp-interruption thread writing set_current, both on
    # the same shared serial connection. Every call must still run to completion (nothing dropped/
    # skipped), and no two calls may ever be "on the wire" at the same time (no interleaving).
    active = 0
    max_concurrent = 0
    guard = threading.Lock()  # protects the counters below, not part of the code under test

    def slow_delegate_call(*args, **kwargs):
        nonlocal active, max_concurrent
        with guard:
            active += 1
            max_concurrent = max(max_concurrent, active)
        time.sleep(0.02)
        with guard:
            active -= 1
        return _fake_response()

    delegate = Mock()
    delegate.is_socket_open.return_value = True
    delegate.read_holding_registers.side_effect = slow_delegate_call
    delegate.write_registers.side_effect = slow_delegate_call

    client = ModbusClient(delegate, "test", 502)

    reads = 15
    writes = 15
    threads = (
        [threading.Thread(target=client.read_holding_registers, args=(1000, ModbusDataType.UINT_16))
         for _ in range(reads)]
        + [threading.Thread(target=client.write_register, args=(1000, 0)) for _ in range(writes)]
    )
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert delegate.read_holding_registers.call_count == reads
    assert delegate.write_registers.call_count == writes
    assert max_concurrent == 1
