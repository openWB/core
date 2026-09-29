from unittest.mock import MagicMock, Mock, call

import pytest

from modules.common.component_state import InverterState
from modules.common.component_type import ComponentType
from modules.devices.enecess.ecomain import config, inverter
from modules.devices.enecess.ecomain.config import (
    EcoMainChannelConfiguration,
    EcoMainInverterConfiguration,
    EcoMainInverterSetup,
)
from modules.devices.enecess.ecomain.runtime import EcoMainChannelReading, EcoMainRuntime


@pytest.mark.parametrize(
    "invert, expected_state, expected_filter_values",
    [
        (
            False,
            InverterState(
                power=-500,
                currents=[0, 0, -2.5],
                exported=1200,
                imported=40,
                serial_number="099806571330_inv_l3-h-c01",
            ),
            (-500, 40, 1200),
        ),
        (
            True,
            InverterState(
                power=500,
                currents=[0, 0, 2.5],
                exported=40,
                imported=1200,
                serial_number="099806571330_inv_l3-h-c01",
            ),
            (500, 1200, 40),
        ),
    ],
)
def test_single_phase_update_applies_direction(
        monkeypatch, invert, expected_state, expected_filter_values):
    value_store = Mock()
    monkeypatch.setattr(
        inverter,
        "get_component_value_store",
        Mock(return_value=value_store),
    )
    peak_filter = Mock()
    peak_filter.check_values.return_value = expected_filter_values[1:]
    peak_filter_factory = Mock(return_value=peak_filter)
    monkeypatch.setattr(inverter, "PeakFilter", peak_filter_factory)
    validator = Mock(wraps=config.validate_inverter_configuration)
    monkeypatch.setattr(inverter.config, "validate_inverter_configuration", validator)
    runtime = MagicMock(spec=EcoMainRuntime)
    runtime.device_serial = "099806571330"
    runtime.read_channel.return_value = EcoMainChannelReading(
        power=500,
        current=2.5,
        forward_energy=1200,
        reverse_energy=40,
    )
    component_config = EcoMainInverterSetup(
        id=7,
        configuration=EcoMainInverterConfiguration(
            phase_count=1,
            invert=invert,
            channels=[EcoMainChannelConfiguration(phase=3, source=0, channel=1)],
        ),
    )
    component = inverter.EcoMainInverter(component_config, runtime, device_id=1)

    component.initialize()
    component.update()

    validator.assert_called_once_with(component_config.configuration)
    runtime.ensure_compatible.assert_called_once_with()
    runtime.read_channel.assert_called_once_with(0, 1)
    peak_filter_factory.assert_called_once_with(
        ComponentType.INVERTER,
        component_config.id,
        component.fault_state,
    )
    peak_filter.check_values.assert_called_once_with(*expected_filter_values)
    assert value_store.set.call_count == 1
    assert vars(value_store.set.call_args.args[0]) == vars(expected_state)


def test_three_phase_read_sorts_channels_and_aggregates_values(monkeypatch):
    peak_filter = Mock()
    peak_filter.check_values.return_value = (600, 6000)
    monkeypatch.setattr(inverter, "PeakFilter", Mock(return_value=peak_filter))
    runtime = MagicMock(spec=EcoMainRuntime)
    runtime.device_serial = "099806571330"
    runtime.read_channel.side_effect = [
        EcoMainChannelReading(100, 1, 1000, 100),
        EcoMainChannelReading(200, 2, 2000, 200),
        EcoMainChannelReading(300, 3, 3000, 300),
    ]
    component_config = EcoMainInverterSetup(
        id=8,
        configuration=EcoMainInverterConfiguration(
            phase_count=3,
            channels=[
                EcoMainChannelConfiguration(phase=3, source=2, channel=10),
                EcoMainChannelConfiguration(phase=1, source=0, channel=1),
                EcoMainChannelConfiguration(phase=2, source=1, channel=3),
            ],
        ),
    )
    component = inverter.EcoMainInverter(component_config, runtime, device_id=1)

    component.initialize()
    state = component.read_state()

    assert runtime.read_channel.call_args_list == [call(0, 1), call(1, 3), call(2, 10)]
    peak_filter.check_values.assert_called_once_with(-600, 600, 6000)
    assert vars(state) == vars(InverterState(
        power=-600,
        currents=[-1, -2, -3],
        exported=6000,
        imported=600,
        serial_number="099806571330_inv_l1-h-c01_l2-s1-c03_l3-s2-c10",
    ))
