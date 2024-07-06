from control import data
from helpermodules.measurement_logging.update_yields import update_module_yields


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
