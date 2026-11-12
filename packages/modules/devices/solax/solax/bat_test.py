from types import SimpleNamespace
from unittest.mock import Mock

from modules.devices.solax.solax import bat
from modules.devices.solax.solax.config import Solax, SolaxBatConfiguration, SolaxBatSetup, SolaxConfiguration
from modules.devices.solax.solax.version import SolaxVersion


def _create_solax_bat(version: SolaxVersion, battery_index: int = 1, client=None) -> bat.SolaxBat:
    config = SolaxConfiguration(version=version)
    device_config = Solax(configuration=config)
    component_config = SolaxBatSetup(configuration=SolaxBatConfiguration(battery_index=battery_index))
    return bat.SolaxBat(component_config, device_config=device_config, client=client or SimpleNamespace())


def test_get_mode4_push_power_stop_is_zero() -> None:
    solax_bat = _create_solax_bat(SolaxVersion.G3)
    assert solax_bat._get_mode4_push_power(0) == 0


def test_get_mode4_push_power_discharge_is_positive() -> None:
    solax_bat = _create_solax_bat(SolaxVersion.G3)
    assert solax_bat._get_mode4_push_power(-700) == 700


def test_get_mode4_push_power_charge_is_negative() -> None:
    solax_bat = _create_solax_bat(SolaxVersion.G3)
    assert solax_bat._get_mode4_push_power(1000) == -1000


def test_power_limit_controllable_true_for_g3() -> None:
    solax_bat = _create_solax_bat(SolaxVersion.G3)
    assert solax_bat.power_limit_controllable() is True


def test_power_limit_controllable_false_for_g2() -> None:
    solax_bat = _create_solax_bat(SolaxVersion.G2)
    assert solax_bat.power_limit_controllable() is False


def test_power_limit_controllable_false_for_g4() -> None:
    solax_bat = _create_solax_bat(SolaxVersion.G4)
    assert solax_bat.power_limit_controllable() is False


def test_update_reads_first_battery_registers_by_default() -> None:
    client = Mock()
    client.read_input_registers.side_effect = [500, 80]
    solax_bat = _create_solax_bat(SolaxVersion.G5, battery_index=1, client=client)
    solax_bat.initialize()

    solax_bat.update()

    client.read_input_registers.assert_any_call(0x0016, bat.ModbusDataType.INT_16, unit=1)
    client.read_input_registers.assert_any_call(0x001C, bat.ModbusDataType.UINT_16, unit=1)


def test_update_reads_second_battery_registers_when_configured() -> None:
    client = Mock()
    client.read_input_registers.side_effect = [500, 80]
    solax_bat = _create_solax_bat(SolaxVersion.G5, battery_index=2, client=client)
    solax_bat.initialize()

    solax_bat.update()

    client.read_input_registers.assert_any_call(297, bat.ModbusDataType.INT_16, unit=1)
    client.read_input_registers.assert_any_call(302, bat.ModbusDataType.UINT_16, unit=1)
