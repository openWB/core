from unittest.mock import MagicMock, Mock

from modules.common.component_state import CounterState
from modules.common.component_type import ComponentType
from modules.devices.enecess.ecomain import counter
from modules.devices.enecess.ecomain.config import EcoMainCounterSetup
from modules.devices.enecess.ecomain.runtime import EcoMainCounterReading, EcoMainRuntime


def test_counter_update_maps_complete_evu_reading(monkeypatch):
    value_store = Mock()
    monkeypatch.setattr(
        counter,
        "get_component_value_store",
        Mock(return_value=value_store),
    )
    peak_filter = Mock()
    peak_filter.check_values.return_value = (1234, 56)
    peak_filter_factory = Mock(return_value=peak_filter)
    monkeypatch.setattr(counter, "PeakFilter", peak_filter_factory)
    runtime = MagicMock(spec=EcoMainRuntime)
    runtime.device_serial = "099806571330"
    runtime.read_counter.return_value = EcoMainCounterReading(
        power=600,
        powers=[100, 200, 300],
        voltages=[230, 231, 232],
        currents=[1, 2, 3],
        power_factors=[0.98, 0.99, 1.0],
        imported=1234,
        exported=56,
    )
    component_config = EcoMainCounterSetup(id=4)
    component = counter.EcoMainCounter(component_config, runtime, device_id=1)

    component.initialize()
    component.update()

    runtime.ensure_compatible.assert_called_once_with()
    peak_filter_factory.assert_called_once_with(
        ComponentType.COUNTER,
        component_config.id,
        component.fault_state,
    )
    peak_filter.check_values.assert_called_once_with(600, 1234, 56)
    expected = CounterState(
        power=600,
        powers=[100, 200, 300],
        voltages=[230, 231, 232],
        currents=[1, 2, 3],
        power_factors=[0.98, 0.99, 1.0],
        imported=1234,
        exported=56,
        frequency=50,
        serial_number="099806571330_evu",
    )
    assert value_store.set.call_count == 1
    assert vars(value_store.set.call_args.args[0]) == vars(expected)
