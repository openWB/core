from datetime import datetime, timezone

from modules.vehicles.myskoda.api import extract_captured_timestamp, extract_warning


def _data(charging_care_mode=None, target_soc=None):
    settings = {}
    if charging_care_mode is not None:
        settings["chargingCareMode"] = charging_care_mode
    if target_soc is not None:
        settings["targetStateOfChargeInPercent"] = target_soc
    return {"vehicle": {"charging": {"settings": settings}}}


def test_extract_captured_timestamp_without_charging_returns_none():
    assert extract_captured_timestamp({"vehicle": {}}) is None


def test_extract_captured_timestamp_missing_field_returns_none():
    assert extract_captured_timestamp({"vehicle": {"charging": {}}}) is None


def test_extract_captured_timestamp_parses_iso8601_with_z_suffix():
    data = {"vehicle": {"charging": {"carCapturedTimestamp": "2021-06-01T12:00:00Z"}}}
    expected = datetime(2021, 6, 1, 12, 0, 0, tzinfo=timezone.utc).timestamp()
    assert extract_captured_timestamp(data) == expected


def test_extract_captured_timestamp_non_string_returns_none():
    data = {"vehicle": {"charging": {"carCapturedTimestamp": 12345}}}
    assert extract_captured_timestamp(data) is None


def test_extract_captured_timestamp_invalid_value_returns_none():
    data = {"vehicle": {"charging": {"carCapturedTimestamp": "not-a-date"}}}
    assert extract_captured_timestamp(data) is None


def test_extract_warning_without_settings_returns_none():
    assert extract_warning({"vehicle": {}}) is None


def test_extract_warning_care_mode_deactivated_returns_none():
    data = _data(charging_care_mode="DEACTIVATED", target_soc=80)
    assert extract_warning(data) is None


def test_extract_warning_care_mode_activated_returns_warning():
    data = _data(charging_care_mode="ACTIVATED", target_soc=80)
    warning = extract_warning(data)
    assert warning is not None
    assert "80" in warning


def test_extract_warning_care_mode_activated_without_target_returns_none():
    data = _data(charging_care_mode="ACTIVATED")
    assert extract_warning(data) is None


def test_extract_warning_care_mode_activated_target_100_returns_none():
    data = _data(charging_care_mode="ACTIVATED", target_soc=100)
    assert extract_warning(data) is None
