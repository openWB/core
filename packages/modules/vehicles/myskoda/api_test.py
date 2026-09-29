from modules.vehicles.myskoda.api import extract_warning


def _data(charging_care_mode=None, target_soc=None):
    settings = {}
    if charging_care_mode is not None:
        settings["chargingCareMode"] = charging_care_mode
    if target_soc is not None:
        settings["targetStateOfChargeInPercent"] = target_soc
    return {"vehicle": {"charging": {"settings": settings}}}


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
