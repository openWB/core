from unittest.mock import Mock

from control import data
from helpermodules.measurement_logging import update_yields
from helpermodules.measurement_logging.update_yields import (
    update_module_yields,
    update_pv_monthly_yearly_yields,
)


def test_update_module_yields(daily_log_totals, mock_pub):
    # setup and execution
    [update_module_yields(type, daily_log_totals) for type in ("bat", "counter", "cp", "pv")]

    # evaluation
    data.data.bat_data["bat2"].data.get.daily_imported = 0.0
    data.data.bat_data["bat2"].data.get.daily_exported = 550.0
    data.data.counter_data["counter0"].data.get.daily_imported = 1492.0
    data.data.counter_data["counter0"].data.get.daily_exported = 0.0
    data.data.cp_all_data.data.get.daily_imported = 1920.0
    data.data.cp_all_data.data.get.daily_exported = 0.0
    data.data.cp_data["cp4"].data.get.daily_imported = 384.0
    data.data.cp_data["cp4"].data.get.daily_exported = 0.0
    data.data.cp_data["cp5"].data.get.daily_imported = 192.0
    data.data.cp_data["cp5"].data.get.daily_exported = 0.0
    data.data.cp_data["cp6"].data.get.daily_imported = 0.0
    data.data.cp_data["cp6"].data.get.daily_exported = 0.0
    data.data.pv_all_data.data.get.daily_exported = 251.0
    data.data.pv_data["pv1"].data.get.daily_exported = 251.0


def test_update_pv_monthly_yearly_yields_skips_when_generation_not_finished(monkeypatch):
    # setup
    data.data.system_data = {"system": Mock(data={"log_data_ready": False})}
    get_monthly_mock = Mock()
    get_yearly_mock = Mock()

    monkeypatch.setattr(update_yields, "_get_pv_monthly_yields", get_monthly_mock)
    monkeypatch.setattr(update_yields, "_get_pv_yearly_yields", get_yearly_mock)

    # execution
    update_pv_monthly_yearly_yields({"pv": {"pv1": {"energy_exported": 12}}})

    # evaluation
    get_monthly_mock.assert_not_called()
    get_yearly_mock.assert_not_called()


def test_update_pv_monthly_yearly_yields_with_daily_and_monthly_fallback(monkeypatch, tmp_path):
    # setup
    data.data.system_data = {"system": Mock(data={"log_data_ready": True})}

    parent_path = tmp_path
    daily_log_path = parent_path / "data" / "daily_log"
    daily_log_path.mkdir(parents=True)
    (daily_log_path / "20260201.json").write_text("{}")
    (daily_log_path / "20260214.json").write_text("{}")
    (daily_log_path / "20260215.json").write_text("{}")

    monkeypatch.setattr(update_yields, "_get_parent_path", lambda: parent_path)
    monkeypatch.setattr(update_yields.timecheck, "create_timestamp_YYYY", lambda: "2026")
    monkeypatch.setattr(update_yields.timecheck, "create_timestamp_YYYYMM", lambda: "202602")
    monkeypatch.setattr(update_yields.timecheck, "create_timestamp_YYYYMMDD", lambda: "20260215")
    monkeypatch.setattr(update_yields.timecheck, "get_relative_date_string", lambda _m, month_offset=1: "202602")

    load_daily_mock = Mock(side_effect=[
        {"totals": {"pv": {"pv1": {"energy_exported": 10}}}},
        None,
    ])
    save_daily_mock = Mock(return_value={"totals": {"pv": {"pv1": {"energy_exported": 20}}}})
    load_monthly_mock = Mock(return_value=None)
    get_monthly_mock = Mock(return_value={"totals": {"pv": {"pv1": {"energy_exported": 100}}}})

    monkeypatch.setattr(update_yields, "load_daily_source_totals_content", load_daily_mock)
    monkeypatch.setattr(update_yields, "save_daily_source_totals", save_daily_mock)
    monkeypatch.setattr(update_yields, "load_monthly_source_totals_content", load_monthly_mock)
    monkeypatch.setattr(update_yields, "get_monthly_log", get_monthly_mock)

    daily_totals = {"pv": {"pv1": {"energy_exported": 5}}}

    # execution
    update_pv_monthly_yearly_yields(daily_totals)

    # evaluation
    assert data.data.pv_data["pv1"].data.get.monthly_exported == 35
    assert data.data.pv_data["pv1"].data.get.yearly_exported == 135
    assert data.data.pv_all_data.data.get.monthly_exported == 35
    assert data.data.pv_all_data.data.get.yearly_exported == 135

    assert load_daily_mock.call_count == 2
    save_daily_mock.assert_called_once_with("20260214", saving=True)
    load_monthly_mock.assert_called_once_with("202601")
    get_monthly_mock.assert_called_once_with("202601")
