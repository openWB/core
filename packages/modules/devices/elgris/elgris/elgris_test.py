from unittest.mock import Mock

from modules.common.component_state import BatState, CounterState, InverterState
from modules.common.modbus import ModbusTcpClient_

from modules.common.sdm import SdmRegister
from modules.devices.elgris.elgris.config import Elgris, ElgrisBatSetup, ElgrisCounterSetup, ElgrisInverterSetup
from modules.devices.elgris.elgris.device import create_device


def setup_modbus_mocks(monkeypatch):
    """Setup common Modbus mocks für alle Tests"""
    mock_read_input_registers_bulk = Mock(side_effect=[
        {SdmRegister.VOLTAGE_L1: [231]*3, SdmRegister.CURRENT_L1: [0.5]*3, SdmRegister.POWER_L1: [115]*3},
        {SdmRegister.IMPORTED: 100, SdmRegister.EXPORTED: 200, SdmRegister.FREQUENCY: 50}])
    mock_read_input_registers = Mock(side_effect=[[0.99]*3])

    monkeypatch.setattr(ModbusTcpClient_, "__enter__", Mock())
    monkeypatch.setattr(ModbusTcpClient_, "__exit__", Mock())
    monkeypatch.setattr(ModbusTcpClient_, "read_input_registers_bulk", mock_read_input_registers_bulk)
    monkeypatch.setattr(ModbusTcpClient_, "read_input_registers", mock_read_input_registers)


def test_elgris_bat(monkeypatch):
    setup_modbus_mocks(monkeypatch)

    elgris_bat = ElgrisBatSetup()
    device = create_device(Elgris())
    device.add_component(elgris_bat)

    store_bat_mock = Mock()
    monkeypatch.setattr(device.components["component0"], "store", store_bat_mock)

    # execution
    device.update()

    # evaluation
    assert vars(store_bat_mock.set.call_args[0][0]) == vars(BatState(
        exported=200000,
        imported=100000,
        power=345,
        currents=[0.5]*3,
    ))


def test_elgris_counter(monkeypatch):
    setup_modbus_mocks(monkeypatch)

    device = create_device(Elgris())
    device.add_component(ElgrisCounterSetup(id=1))

    store_counter_mock = Mock()
    monkeypatch.setattr(device.components["component1"], "store", store_counter_mock)

    # execution
    device.update()

    # evaluation
    assert vars(store_counter_mock.set.call_args[0][0]) == vars(CounterState(
        exported=200000,
        imported=100000,
        power=345,
        voltages=[231]*3,
        currents=[0.5]*3,
        powers=[115]*3,
        power_factors=[0.99]*3,
        frequency=50,
        serial_number=""
    ))


def test_elgris_inverter(monkeypatch):
    setup_modbus_mocks(monkeypatch)

    device = create_device(Elgris())
    device.add_component(ElgrisInverterSetup(id=2))

    store_inverter_mock = Mock()
    monkeypatch.setattr(device.components["component2"], "store", store_inverter_mock)

    # execution
    device.update()

    # evaluation
    assert vars(store_inverter_mock.set.call_args[0][0]) == vars(InverterState(
        exported=200000,
        imported=100000,
        power=345,
        currents=[0.5]*3,
    ))
