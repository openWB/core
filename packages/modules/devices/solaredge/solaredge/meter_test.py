from typing import List, NamedTuple
from unittest.mock import Mock
import pytest

from modules.devices.solaredge.solaredge.config import SolaredgeCounterSetup
from modules.devices.solaredge.solaredge.counter import SolaredgeCounter
from modules.devices.solaredge.solaredge.meter import SolaredgeMeterRegisters, _set_registers


Params = NamedTuple("Params", [("meter_id", int),
                               ("synergy_units", int),
                               ("expected_power_register", int)])

cases = [Params(meter_id=1, synergy_units=1, expected_power_register=40206),
         Params(meter_id=2, synergy_units=1, expected_power_register=40380),
         Params(meter_id=3, synergy_units=1, expected_power_register=40554),
         Params(meter_id=1, synergy_units=2, expected_power_register=40256),
         Params(meter_id=1, synergy_units=3, expected_power_register=40276),
         Params(meter_id=2, synergy_units=2, expected_power_register=40430),
         ]


@pytest.mark.parametrize("params", cases, ids=str)
def test_meter(params: Params):
    # setup and execution
    registers = SolaredgeMeterRegisters(params.meter_id, params.synergy_units)

    # assert
    assert registers.power == params.expected_power_register


Params = NamedTuple("Params", [("configured_meter_ids", List[int])])


@pytest.mark.parametrize(["params"], [
    pytest.param(
        Params(configured_meter_ids=[1, 2]),
        id="ids unchanged if meter_ids are continuous starting from 1"
    ),
    pytest.param(
        Params(configured_meter_ids=[2, 3]),
        id="ids move forward if not starting at 1"
    ),
    pytest.param(
        Params(configured_meter_ids=[1, 3]),
        id="gaps in ids are closed"
    )
])
def test_set_component_registers_assigns_effective_meter_regs(params: Params):
    # setup
    components_list = []
    for meter_id in params.configured_meter_ids:
        counter = SolaredgeCounter(component_config=Mock(spec=SolaredgeCounterSetup,
                                                         configuration=Mock(meter_id=meter_id, modbus_id=1)))
        counter.component_config.configure_mock(name="counter")
        components_list.append(counter)

    for counter in components_list:
        counter.registers = SolaredgeMeterRegisters(internal_meter_id=counter.component_config.configuration.meter_id)
    # execution
    _set_registers(components_list, synergy_units=1, modbus_id=1)

    # evaluation
    assert components_list[0].registers.power == 40206
    assert components_list[1].registers.power == 40380
