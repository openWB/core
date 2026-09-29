from unittest.mock import MagicMock, Mock

from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.modbus import ModbusTcpClient_
from modules.devices.enecess.ecomain import counter, device, inverter
from modules.devices.enecess.ecomain.config import (
    EcoMain,
    EcoMainChannelConfiguration,
    EcoMainConfiguration,
    EcoMainCounterSetup,
    EcoMainInverterConfiguration,
    EcoMainInverterSetup,
)
from modules.devices.enecess.ecomain.runtime import EcoMainRuntime


def _component_mock(component_id: int, name: str, component_type: str) -> Mock:
    component = Mock()
    component.fault_state = FaultState(
        ComponentInfo(component_id, name, component_type)
    )
    component.fault_state.store_error = Mock()
    return component


def test_device_components_share_runtime_and_update_connection(monkeypatch):
    runtime = Mock()
    runtime.client = MagicMock()
    runtime_factory = Mock(return_value=runtime)
    counter_component = _component_mock(1, "counter", "counter")
    inverter_component = _component_mock(2, "inverter", "inverter")
    counter_factory = Mock(return_value=counter_component)
    inverter_factory = Mock(return_value=inverter_component)
    monkeypatch.setattr(device, "EcoMainRuntime", runtime_factory)
    monkeypatch.setattr(device, "EcoMainCounter", counter_factory)
    monkeypatch.setattr(device, "EcoMainInverter", inverter_factory)
    device_config = EcoMain(
        id=7,
        configuration=EcoMainConfiguration("192.0.2.1", "eco-serial"),
    )

    configurable_device = device.create_device(device_config)
    configurable_device.add_component(EcoMainCounterSetup(id=1))
    configurable_device.add_component(EcoMainInverterSetup(id=2))

    runtime_factory.assert_called_once_with("192.0.2.1", "eco-serial")
    assert counter_factory.call_args.kwargs["runtime"] is runtime
    assert inverter_factory.call_args.kwargs["runtime"] is runtime
    assert counter_factory.call_args.kwargs["device_id"] == 7
    assert inverter_factory.call_args.kwargs["device_id"] == 7

    counter_component.initialized = True
    inverter_component.initialized = True
    configurable_device.update()

    runtime.client.__enter__.assert_called_once_with()
    runtime.client.__exit__.assert_called_once()
    counter_component.update.assert_called_once_with()
    inverter_component.update.assert_called_once_with()


def test_device_update_uses_one_client_context_for_real_component_reads(monkeypatch):
    client = MagicMock(spec=ModbusTcpClient_)
    runtime = EcoMainRuntime(
        "192.0.2.1",
        "099806571330",
        client=client,
    )
    runtime._validated = True
    runtime._device_serial = "099806571330"
    runtime._read = Mock(side_effect=[
        1_000, 0, [0, 0, 0, 0], [23000, 0, 100] * 3,
        0, 0, 0, 0,
    ])
    monkeypatch.setattr(device, "EcoMainRuntime", Mock(return_value=runtime))
    monkeypatch.setattr(counter, "get_component_value_store", Mock(return_value=Mock()))
    monkeypatch.setattr(inverter, "get_component_value_store", Mock(return_value=Mock()))
    counter_filter = Mock()
    counter_filter.check_values.return_value = (1, 0)
    inverter_filter = Mock()
    inverter_filter.check_values.return_value = (0, 0)
    monkeypatch.setattr(counter, "PeakFilter", Mock(return_value=counter_filter))
    monkeypatch.setattr(inverter, "PeakFilter", Mock(return_value=inverter_filter))
    monkeypatch.setattr(FaultState, "store_error", Mock())
    configurable_device = device.create_device(EcoMain(
        id=7,
        configuration=EcoMainConfiguration("192.0.2.1", "099806571330"),
    ))
    configurable_device.add_component(EcoMainCounterSetup(id=1))
    configurable_device.add_component(EcoMainInverterSetup(
        id=2,
        configuration=EcoMainInverterConfiguration(
            channels=[EcoMainChannelConfiguration()],
        ),
    ))

    configurable_device.update()

    client.__enter__.assert_called_once_with()
    client.__exit__.assert_called_once()
    assert runtime._read.call_count == 8
