import logging

from modules.devices.shelly.shelly.status_handler import parse_temperatures

# real status dump from a Shelly Plug S without external temp probes attached (Discussion #3466,
# discussioncomment-19500699): ext_temperature is an empty dict, not missing/malformed data
GEN1_STATUS_WITHOUT_EXT_SENSORS = {
    "temperature": 38.73,
    "tmp": {"tC": 38.73, "tF": 101.71, "is_valid": True},
    "ext_sensors": {},
    "ext_temperature": {},
    "ext_humidity": {},
}


def test_parse_temperatures_returns_none_without_logging_error_when_no_ext_sensors(caplog):
    with caplog.at_level(logging.ERROR):
        result = parse_temperatures(GEN1_STATUS_WITHOUT_EXT_SENSORS, generation=1)

    assert result is None
    assert caplog.records == []


def test_parse_temperatures_gen1_reads_available_ext_sensors():
    status = {"ext_temperature": {"0": {"tC": 21.5}, "2": {"tC": 22.1}}}

    result = parse_temperatures(status, generation=1)

    assert result == [21.5, 22.1]


def test_parse_temperatures_still_logs_on_genuinely_malformed_value(caplog):
    status = {"ext_temperature": {"0": {"tC": "not-a-number"}}}

    with caplog.at_level(logging.ERROR):
        result = parse_temperatures(status, generation=1)

    assert result is None
    assert len(caplog.records) == 1


def test_parse_temperatures_gen2_without_ext_sensors_does_not_log(caplog):
    with caplog.at_level(logging.ERROR):
        result = parse_temperatures({}, generation=2)

    assert result is None
    assert caplog.records == []
