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


def test_caddy_uses_its_measurement_timestamp_instead_of_latest_other_field():
    data = BASE_DATA + [{
        "key": "ae0294b4-1286-3e98-a818-1485b8d88430", "dataFieldName": "state_of_charge",
        "value": 0, "timestampUtc": "2026-09-15T08:00:00Z",
    }]
    result = parse_vehicle_data({"Data": data})
    assert result["soc"] == 0
    assert result["soc_timestamp_str"] == "2026-09-15T08:00:00Z"
    assert result["soc_timestamp"] == 1789459200


def test_fallback_fields_and_latest_capture_time_are_preserved():
    data = [
        {"key": "506cb83e-f99f-3af3-bbeb-0429b69a78d9", "dataFieldName": "soc", "value": "42"},
        {"key": "55e0d40b-38ed-3cb5-9dcd-6193df6fc493", "dataFieldName": "range", "value": 0},
        {"key": "30cc36fd-71ca-3c09-9296-e94ebd47bd2b", "dataFieldName": "odometer", "value": "1000"},
        {"key": "new", "dataFieldName": "car_captured_time", "value": "2026-09-15T09:00:00Z"},
        {"key": "old", "dataFieldName": "car_captured_time", "value": "2026-09-15T08:00:00Z"},
    ]
    result = parse_vehicle_data({"Data": data})
    assert (result["soc"], result["range"], result["odometer"]) == ("42", 0, "1000")
    assert result["soc_timestamp_str"] == "2026-09-15T09:00:00Z"


def test_primary_zero_soc_takes_precedence_over_fallback():
    data = [dict(field) for field in BASE_DATA]
    data[1]["value"] = 0
    data.append({"key": "506cb83e-f99f-3af3-bbeb-0429b69a78d9", "dataFieldName": "soc", "value": "99"})
    assert parse_vehicle_data({"Data": data})["soc"] == 0


def test_generic_timestamp_is_not_used_without_car_captured_time():
    data = [BASE_DATA[1]] + [
        {"key": "latest", "dataFieldName": "timestamp", "value": "2026-09-15T09:00:00Z"},
        {"key": "earlier", "dataFieldName": "timestamp", "value": "2026-09-15T08:00:00Z"},
    ]
    result = parse_vehicle_data({"Data": data})
    assert result["soc"] == "55.0"
    assert result["soc_timestamp_str"] is None
    assert result["soc_timestamp"] is None


def test_car_captured_time_is_used_despite_newer_generic_timestamp():
    data = BASE_DATA + [
        {"key": "fallback", "dataFieldName": "timestamp", "value": "2026-09-15T10:00:00Z"},
    ]
    result = parse_vehicle_data({"Data": data})
    assert result["soc_timestamp_str"] == "2026-09-15T09:00:00Z"


def test_caddy_timestamp_is_used_without_car_captured_time():
    data = [
        {"key": "ae0294b4-1286-3e98-a818-1485b8d88430", "dataFieldName": "state_of_charge",
         "value": 55, "timestampUtc": "2026-09-15T08:00:00Z"},
        {"key": "fallback", "dataFieldName": "timestamp", "value": "2026-09-15T10:00:00Z"},
    ]
    result = parse_vehicle_data({"Data": data})
    assert result["soc_timestamp_str"] == "2026-09-15T08:00:00Z"


def test_missing_timestamp_fields_returns_no_timestamp():
    result = parse_vehicle_data({"Data": [BASE_DATA[1]]})
    assert result["soc_timestamp"] is None
    assert result["soc_timestamp_str"] is None
