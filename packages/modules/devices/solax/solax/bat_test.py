from types import SimpleNamespace

from modules.devices.solax.solax import bat
from modules.devices.solax.solax.config import Solax, SolaxBatSetup, SolaxConfiguration
from modules.devices.solax.solax.version import SolaxVersion


def _create_solax_bat(version: SolaxVersion) -> bat.SolaxBat:
    config = SolaxConfiguration(version=version)
    device_config = Solax(configuration=config)
    return bat.SolaxBat(SolaxBatSetup(), device_config=device_config, client=SimpleNamespace())


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
