from unittest.mock import Mock

import pytest

from control import data
from modules.io_actions.generator_systems.stepwise_control.api_eebus import StepwiseControlEebus
from modules.io_actions.generator_systems.stepwise_control.config import StepwiseControlConfig, StepwiseControlSetup


@pytest.fixture()
def mock_data() -> None:
    data.data_init(Mock())


def _build_action(lpp_value: float, max_ac_out: float) -> StepwiseControlEebus:
    config = StepwiseControlSetup(configuration=StepwiseControlConfig(
        io_device=0,
        devices=[{"type": "inverter", "id": 1}],
    ))
    action = StepwiseControlEebus(config)
    action.lpp_value = lpp_value
    data.data.pv_data["pv1"] = Mock(data=Mock(config=Mock(max_ac_out=max_ac_out)))
    return action


@pytest.mark.parametrize(
    "lpp_value,max_ac_out,expected",
    [
        pytest.param(0, 10000, 0, id="0W -> 0%"),
        pytest.param(1000, 10000, 0.3, id="10% -> 30%"),
        pytest.param(3000, 10000, 0.3, id="30% -> 30%"),
        pytest.param(4500, 10000, 0.6, id="45% -> 60%"),
        pytest.param(6000, 10000, 0.6, id="60% -> 60%"),
        pytest.param(9000, 10000, 1.0, id="90% -> 100%"),
    ],
)
def test_get_step(mock_data, lpp_value, max_ac_out, expected):
    action = _build_action(lpp_value=lpp_value, max_ac_out=max_ac_out)

    assert action.get_step() == expected


def test_get_step_handles_zero_division(mock_data):
    action = _build_action(lpp_value=5000, max_ac_out=0)

    assert action.get_step() == 0
