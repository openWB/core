from types import SimpleNamespace

from modules.devices.qcells.qcells import bat
from modules.devices.qcells.qcells.config import QCellsBatSetup


def _fake_data(
    home_consumption: int,
    cp_power: int,
    pv_power: int,
    bat_power: int,
    evu_power: int,
    import_limit: int,
) -> SimpleNamespace:
    evu_counter = SimpleNamespace(
        data=SimpleNamespace(
            get=SimpleNamespace(power=evu_power),
            config=SimpleNamespace(max_total_power=import_limit),
        )
    )
    return SimpleNamespace(
        counter_all_data=SimpleNamespace(
            data=SimpleNamespace(set=SimpleNamespace(home_consumption=home_consumption)),
            get_evu_counter=lambda: evu_counter,
        ),
        cp_all_data=SimpleNamespace(data=SimpleNamespace(get=SimpleNamespace(power=cp_power))),
        pv_all_data=SimpleNamespace(data=SimpleNamespace(get=SimpleNamespace(power=pv_power))),
        bat_all_data=SimpleNamespace(data=SimpleNamespace(get=SimpleNamespace(power=bat_power))),
    )


def _create_qcells_bat() -> bat.QCellsBat:
    return bat.QCellsBat(QCellsBatSetup(), modbus_id=1, client=SimpleNamespace())


def test_get_active_power_target_stop_is_zero(monkeypatch) -> None:
    qcells_bat = _create_qcells_bat()
    monkeypatch.setattr(
        bat.data,
        "data",
        _fake_data(
            home_consumption=450,
            cp_power=5500,
            pv_power=-5600,
            bat_power=-200,
            evu_power=100,
            import_limit=24000,
        ),
        raising=False,
    )

    assert qcells_bat._get_active_power_target(0) == 0


def test_get_active_power_target_discharge_keeps_limit(monkeypatch) -> None:
    qcells_bat = _create_qcells_bat()
    monkeypatch.setattr(
        bat.data,
        "data",
        _fake_data(
            home_consumption=500,
            cp_power=4800,
            pv_power=-5200,
            bat_power=-900,
            evu_power=-300,
            import_limit=24000,
        ),
        raising=False,
    )

    assert qcells_bat._get_active_power_target(-700) == -700


def test_get_active_power_target_charge_clamped_by_import_limit(monkeypatch) -> None:
    qcells_bat = _create_qcells_bat()
    monkeypatch.setattr(
        bat.data,
        "data",
        _fake_data(
            home_consumption=600,
            cp_power=5400,
            pv_power=-4000,
            bat_power=300,
            evu_power=1800,
            import_limit=6200,
        ),
        raising=False,
    )

    assert qcells_bat._get_active_power_target(1200) == 200


def test_get_active_power_target_charge_clamped_to_zero_without_headroom(monkeypatch) -> None:
    qcells_bat = _create_qcells_bat()
    monkeypatch.setattr(
        bat.data,
        "data",
        _fake_data(
            home_consumption=800,
            cp_power=5200,
            pv_power=-4500,
            bat_power=100,
            evu_power=5800,
            import_limit=5000,
        ),
        raising=False,
    )

    assert qcells_bat._get_active_power_target(1000) == 0
