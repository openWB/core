import sys
from unittest.mock import MagicMock, Mock

import pytest

from modules.common.component_state import CounterState
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.fault_state_level import FaultStateLevel
from modules.internal_chargepoint_handler import local_socket as socket_module


@pytest.fixture
def socket(monkeypatch):
    instance = socket_module.LocalSocket()
    instance._meter_fault = FaultState(ComponentInfo(None, "Testmessung", "consumer"))
    instance._gpio = Mock(HIGH=1, LOW=0)
    instance._meter = Mock()
    instance._client = instance._meter.client
    instance._meter.client.read_input_registers.return_value = 230
    instance._meter.get_counter_state.return_value = CounterState(
        power=500, imported=1234, exported=0, currents=[2.2, 0, 0], voltages=[230, 0, 0])
    return instance


def test_switch_on_requires_successful_measurement(socket):
    with pytest.raises(FaultState):
        socket.switch(True)
    socket._gpio.output.assert_not_called()


def test_poll_and_switch_return_hardware_energy_and_independent_relay_state(socket):
    socket._meter.get_counter_state.return_value.power = 0
    socket.poll()
    socket.switch(True)
    state = socket.get_state()
    assert state.state is True
    assert state.power == 0
    assert state.imported == 1234
    socket._gpio.output.assert_called_with(26, 1)
    socket.switch(False)
    assert socket.get_state().state is False


def test_missing_meter_is_retried_slowly_and_does_not_raise_into_chargepoint(socket):
    socket._meter.client.read_input_registers.side_effect = TimeoutError("no response")
    socket.poll()
    socket.poll()
    assert socket._meter.client.read_input_registers.call_count == 1
    assert socket._present is False
    with pytest.raises(FaultState) as error:
        socket.get_state()
    assert "nicht erreichbar" in error.value.fault_str
    assert error.value.fault_state == FaultStateLevel.ERROR


def test_measurement_failure_switches_output_off(socket):
    socket.poll()
    socket.switch(True)
    socket._next_poll = 0
    socket._meter.get_counter_state.side_effect = TimeoutError("no response")
    socket.poll()
    socket._gpio.output.assert_any_call(26, 0)
    socket._gpio.output.assert_called_with(23, 0)
    assert socket._state is False


def test_meter_constructor_failure_is_isolated_from_chargepoint(socket, monkeypatch):
    socket._meter = None
    monkeypatch.setattr(socket_module, "Sdm120", Mock(side_effect=TimeoutError("serial number unavailable")))
    socket.poll()
    assert socket._present is False
    assert "serial number unavailable" in socket.get_fault()[1]
    with pytest.raises(FaultState):
        socket.switch(True)


def test_stale_measurement_cannot_enable_output(socket, monkeypatch):
    socket.poll()
    socket.switch(True)
    monkeypatch.setattr(socket_module.time, "monotonic", lambda: socket._timestamp + 16)
    with pytest.raises(FaultState) as error:
        socket.switch(True)
    assert "veraltet" in error.value.fault_str
    socket._gpio.output.assert_any_call(26, 0)


def test_recovery_refreshes_values_but_does_not_switch_on(socket):
    socket.poll()
    socket.switch(True)
    socket._next_poll = 0
    socket._meter.get_counter_state.side_effect = TimeoutError("no response")
    socket.poll()
    socket._next_poll = 0
    socket._meter.get_counter_state.side_effect = None
    socket.poll()
    assert socket.get_state().state is False


def test_stop_clears_availability_and_switches_off(socket):
    socket.poll()
    socket.switch(True)
    socket.stop()
    socket._gpio.output.assert_any_call(26, 0)
    with pytest.raises(FaultState) as error:
        socket.get_state()
    assert "nicht aktiv" in error.value.fault_str


def test_handler_restart_resets_output_and_cached_measurements(socket, monkeypatch):
    socket.poll()
    socket.switch(True)
    gpio = socket._gpio
    monkeypatch.setitem(sys.modules, "RPi", Mock(GPIO=gpio))
    monkeypatch.setitem(sys.modules, "RPi.GPIO", gpio)
    socket.start(Mock(), Mock())
    gpio.setup.assert_any_call(26, gpio.OUT, initial=0)
    gpio.setup.assert_any_call(23, gpio.OUT, initial=0)
    assert socket._state is False
    assert socket._values is None
    with pytest.raises(FaultState):
        socket.switch(True)


@pytest.fixture
def consumer(socket, monkeypatch):
    from helpermodules.subdata import SubData
    from modules.common import configurable_consumer, fault_state
    from modules.consumers.generic.gpio_sdm120 import consumer as module
    from modules.consumers.generic.gpio_sdm120.config import GpioSdm120

    monkeypatch.setattr(SubData, "consumer_data", {})
    monkeypatch.setattr(module, "local_socket", socket)
    monkeypatch.setattr(configurable_consumer, "get_component_value_store", Mock())
    monkeypatch.setattr(configurable_consumer, "SimCounterConsumer", Mock())
    peak_filter = Mock()
    peak_filter.check_values.return_value = (1234, 0)
    monkeypatch.setattr(configurable_consumer, "PeakFilter", Mock(return_value=peak_filter))
    publisher = Mock()
    monkeypatch.setattr(fault_state, "Pub", Mock(return_value=publisher))
    return module.create_consumer(GpioSdm120(id=2)), publisher


def test_failed_measurement_is_published_as_regular_consumer_fault(socket, consumer):
    module, publisher = consumer
    socket._meter.get_counter_state.side_effect = TimeoutError("no response")
    socket.poll()
    publisher.pub.assert_not_called()
    module.update()
    assert module.fault_state.fault_state == FaultStateLevel.ERROR
    assert "no response" in module.fault_state.fault_str
    publisher.pub.assert_any_call("openWB/set/consumer/2/get/fault_state", 2)
    assert {call.args[0] for call in publisher.pub.call_args_list} == {
        "openWB/set/consumer/2/get/fault_state", "openWB/set/consumer/2/get/fault_str"}
    module.store.set.assert_not_called()


def test_switch_off_does_not_clear_measurement_error(socket, consumer):
    module, publisher = consumer
    module.switch_off()
    assert module.fault_state.fault_state == FaultStateLevel.ERROR
    publisher.pub.assert_any_call("openWB/set/consumer/2/get/fault_state", 2)


def test_warning_and_recovery_are_transferred_to_consumer(socket, consumer):
    module, publisher = consumer
    values = socket._meter.get_counter_state.return_value

    def read_warning():
        socket._meter_fault.warning("Warnung der Steckdosenmessung")
        return values

    socket._meter.get_counter_state.side_effect = read_warning
    socket.poll()
    module.update()
    assert module.fault_state.fault_state == FaultStateLevel.WARNING
    publisher.pub.assert_any_call("openWB/set/consumer/2/get/fault_state", 1)
    module.store.set.assert_called_once()
    socket._meter.get_counter_state.side_effect = None
    socket._next_poll = 0
    socket.poll()
    module.update()
    assert module.fault_state.fault_state == FaultStateLevel.NO_ERROR
    publisher.pub.assert_any_call("openWB/set/consumer/2/get/fault_state", 0)


def test_error_recovery_clears_regular_consumer_fault(socket, consumer):
    module, publisher = consumer
    socket._meter.get_counter_state.side_effect = TimeoutError("no response")
    socket.poll()
    module.update()
    assert module.fault_state.fault_state == FaultStateLevel.ERROR
    socket._meter.get_counter_state.side_effect = None
    socket._next_poll = 0
    socket.poll()
    module.update()
    assert module.fault_state.fault_state == FaultStateLevel.NO_ERROR
    publisher.pub.assert_any_call("openWB/set/consumer/2/get/fault_state", 0)


def test_single_se_does_not_create_unconfigured_second_chargepoint(monkeypatch):
    from modules.internal_chargepoint_handler import internal_chargepoint_handler as handler
    from modules.chargepoints.internal_openwb.config import InternalChargepointMode

    monkeypatch.setattr(handler.InternalChargepointHandler, "init_gpio", Mock())
    monkeypatch.setattr(handler, "SingleComponentUpdateContext", MagicMock())
    factory = Mock()
    monkeypatch.setattr(handler, "client_factory", factory)
    monkeypatch.setattr(handler, "HandlerChargepoint", Mock())
    instance = handler.InternalChargepointHandler(
        InternalChargepointMode.SE, Mock(), Mock(), 1, None, None, Mock(), Mock())
    assert factory.call_count == 1
    assert instance.cp1 is None
    assert instance.cp1_client_handler is None
