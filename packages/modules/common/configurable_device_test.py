from unittest.mock import Mock

from modules.common.component_setup import ComponentSetup
from modules.common.configurable_device import ConfigurableDevice


class FakeComponent:
    store_spec = None  # None = Mock erlaubt beliebige Attribute (zB zero_power_on_sustained_error)

    def __init__(self, component_config):
        self.component_config = component_config

    def initialize(self):
        self.fault_state = Mock(on_sustained_error=None)
        self.store = Mock(spec=self.store_spec) if self.store_spec else Mock()


class FakeComponentWithoutZeroPowerHook(FakeComponent):
    store_spec = ["update"]  # zB Counter: keine zero_power_on_sustained_error()


def _device(component_class=FakeComponent) -> ConfigurableDevice:
    device_config = Mock(id=1, name="Test")
    return ConfigurableDevice(
        device_config=device_config,
        component_factory=lambda config: component_class(config),
        component_updater=Mock(),
    )


def test_add_component_wires_sustained_error_handler():
    # setup
    device = _device()
    component_config = ComponentSetup("Test", "inverter", 1, None)

    # execution
    device.add_component(component_config)

    # evaluation
    component = device.components["component1"]
    assert component.fault_state.on_sustained_error is not None


def test_wired_handler_zeroes_and_publishes():
    # setup
    device = _device()
    component_config = ComponentSetup("Test", "inverter", 1, None)
    device.add_component(component_config)
    component = device.components["component1"]

    # execution
    component.fault_state.on_sustained_error()

    # evaluation
    component.store.zero_power_on_sustained_error.assert_called_once()
    component.store.update.assert_called_once()


def test_wired_handler_tolerates_store_without_zero_power_hook():
    # setup - zB Counter: Store ohne zero_power_on_sustained_error()
    device = _device(FakeComponentWithoutZeroPowerHook)
    component_config = ComponentSetup("Test", "counter", 1, None)
    device.add_component(component_config)
    component = device.components["component1"]

    # execution - darf nicht raisen
    component.fault_state.on_sustained_error()
    component.store.update.assert_not_called()
