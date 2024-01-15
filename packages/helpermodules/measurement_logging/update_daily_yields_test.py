import pytest

from helpermodules.measurement_logging.update_daily_yields import update_module_yields


def test_update_module_yields(daily_log_totals, mock_pub):
    # setup and execution
    [update_module_yields(type, daily_log_totals) for type in ("bat", "counter", "cp", "pv")]

    # evaluation
    expected = {
        "openWB/set/bat/2/get/daily_imported": 0.0,
        "openWB/set/bat/2/get/daily_exported": 550.0,
        "openWB/set/counter/0/get/daily_imported": 1492.0,
        "openWB/set/counter/0/get/daily_exported": 0.0,
        "openWB/set/chargepoint/get/daily_imported": 1920.0,
        "openWB/set/chargepoint/get/daily_exported": 0.0,
        "openWB/set/chargepoint/4/get/daily_imported": 384.0,
        "openWB/set/chargepoint/4/get/daily_exported": 0.0,
        "openWB/set/chargepoint/5/get/daily_imported": 192.0,
        "openWB/set/chargepoint/5/get/daily_exported": 0.0,
        "openWB/set/chargepoint/6/get/daily_imported": 0.0,
        "openWB/set/chargepoint/6/get/daily_exported": 0.0,
        "openWB/set/pv/get/daily_exported": 251.0,
        "openWB/set/pv/1/get/daily_exported": 251.0}
    for topic, value in expected.items():
        for call in mock_pub.mock_calls:
            try:
                if call.args[0] == topic:
                    assert value == call.args[1]
                    break
            except IndexError:
                pass
        else:
            pytest.fail(f"Topic {topic} is missing")
