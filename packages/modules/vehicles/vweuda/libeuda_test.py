from modules.vehicles.vweuda.libeuda import parse_vehicle_data

BASE_DATA = [
    {"key": "k-ts", "dataFieldName": "car_captured_time", "value": "2026-09-15T09:00:00Z"},
    {"key": "ac1108b1-b8cc-3db9-a663-03d387e42223", "dataFieldName": "battery_level_HV.value", "value": "55.0"},
]


def test_parse_vehicle_data_without_bcam_fields_returns_no_warning():
    result = parse_vehicle_data({"Data": BASE_DATA})

    assert result["warning"] is None
    assert result["soc"] == "55.0"


def test_parse_vehicle_data_with_bcam_inactive_returns_no_warning():
    data = BASE_DATA + [
        {"key": "k-bcam", "dataFieldName": "setting.bcam_activation", "value": "BCAM_ACTIVATION_DEACTIVATED"},
        {"key": "k-thr", "dataFieldName": "battery_care_mode.charge_bcam_threshold", "value": "80"},
    ]

    result = parse_vehicle_data({"Data": data})

    assert result["warning"] is None
    assert result["soc"] == "55.0"


def test_parse_vehicle_data_with_bcam_active_returns_warning():
    data = BASE_DATA + [
        {"key": "k-bcam", "dataFieldName": "setting.bcam_activation", "value": "BCAM_ACTIVATION_ACTIVATED"},
        {"key": "k-thr", "dataFieldName": "battery_care_mode.charge_bcam_threshold", "value": "80"},
    ]

    result = parse_vehicle_data({"Data": data})

    assert result["warning"] is not None
    assert "80" in result["warning"]
    assert result["soc"] == "55.0"


def test_parse_vehicle_data_with_bcam_active_but_no_threshold_returns_no_warning():
    data = BASE_DATA + [
        {"key": "k-bcam", "dataFieldName": "setting.bcam_activation", "value": "BCAM_ACTIVATION_ACTIVATED"},
    ]

    result = parse_vehicle_data({"Data": data})

    assert result["warning"] is None
