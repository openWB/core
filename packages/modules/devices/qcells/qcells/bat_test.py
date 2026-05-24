from types import SimpleNamespace

from modules.devices.qcells.qcells import bat
from modules.devices.qcells.qcells.config import QCellsBatSetup


def _create_qcells_bat() -> bat.QCellsBat:
    return bat.QCellsBat(QCellsBatSetup(), modbus_id=1, client=SimpleNamespace())


def test_get_mode4_push_power_stop_is_zero() -> None:
    qcells_bat = _create_qcells_bat()
    assert qcells_bat._get_mode4_push_power(0) == 0


def test_get_mode4_push_power_discharge_is_positive() -> None:
    qcells_bat = _create_qcells_bat()
    # openWB discharge limit is negative -> mode4 push power must be positive
    assert qcells_bat._get_mode4_push_power(-700) == 700


def test_get_mode4_push_power_charge_is_negative() -> None:
    qcells_bat = _create_qcells_bat()
    # openWB charge limit is positive -> mode4 push power must be negative
    assert qcells_bat._get_mode4_push_power(1000) == -1000
