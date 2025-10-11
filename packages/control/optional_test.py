from unittest.mock import Mock
from control.optional import Optional
from helpermodules import timecheck
import pytest

ONE_HOUR_SECONDS = 3600
IGNORED = 0.0001
CHEEP = 0.0002
EXPENSIVE = 0.0003


@pytest.mark.no_mock_full_hour
@pytest.mark.parametrize(
    "granularity, now_ts, duration, remaining_time, price_list, expected_loading_hours",
    [
        pytest.param(
            "full_hour",
            1698228000,
            ONE_HOUR_SECONDS,
            3 * ONE_HOUR_SECONDS,
            {
                "1698224400": 0.00012499,
                "1698228000": 0.00011737999999999999,  # matching now
                "1698231600": 0.00011562000000000001,
                "1698235200": 0.00012447,  # last before plan target
                "1698238800": 0.00013813,
                "1698242400": 0.00014751,
                "1698246000": 0.00015372999999999998,
                "1698249600": 0.00015462,
                "1698253200": 0.00015771,
                "1698256800": 0.00013708,
                "1698260400": 0.00012355,
                "1698264000": 0.00012006,
                "1698267600": 0.00011279999999999999,
            },
            [1698231600],
            id="select single time slot of one hour length"
        ),
        pytest.param(
            "quarter_hour",
            1698226200,
            2 * ONE_HOUR_SECONDS,
            4 * ONE_HOUR_SECONDS,
            {
                # first hour
                "1698224400": IGNORED,
                "1698225300": IGNORED,
                "1698226200": EXPENSIVE,  # current quarert hour
                "1698227100": CHEEP,
                # second hour
                "1698228000": EXPENSIVE,
                "1698228900": EXPENSIVE,
                "1698229800": CHEEP,
                "1698230700": EXPENSIVE,
                # third hour
                "1698231600": CHEEP,
                "1698232500": CHEEP,
                "1698233400": CHEEP,
                "1698234300": EXPENSIVE,
                # fourth hour
                "1698235200": CHEEP,
                "1698236100": EXPENSIVE,
                "1698237000": EXPENSIVE,
                "1698237900": EXPENSIVE,
                # fifth hour
                "1698238800": CHEEP,
                "1698239700": CHEEP,  # last before plan target
                "1698240600": IGNORED,
                "1698241500": IGNORED,
            },
            [1698227100, 1698229800, 1698231600, 1698232500, 1698233400, 1698235200, 1698238800, 1698239700],
            id="select 8 time slots of 15 minutes lenght, include last before plan target"
        ),
        pytest.param(
            "quarter_hour",
            1698227100,
            2 * ONE_HOUR_SECONDS,
            4 * ONE_HOUR_SECONDS,
            {
                # first hour
                "1698224400": IGNORED,
                "1698225300": IGNORED,
                "1698226200": EXPENSIVE,
                "1698227100": CHEEP,  # current quarert hour
                # second hour
                "1698228000": EXPENSIVE,
                "1698228900": EXPENSIVE,
                "1698229800": CHEEP,
                "1698230700": EXPENSIVE,
                # third hour
                "1698231600": CHEEP,
                "1698232500": CHEEP,
                "1698233400": CHEEP,
                "1698234300": EXPENSIVE,
                # fourth hour
                "1698235200": CHEEP,
                "1698236100": EXPENSIVE,
                "1698237000": EXPENSIVE,
                "1698237900": EXPENSIVE,
                # fifth hour
                "1698238800": CHEEP,
                "1698239700": CHEEP,
                "1698240600": EXPENSIVE,  # last before plan target
                "1698241500": IGNORED,
            },
            [1698227100, 1698229800, 1698231600, 1698232500, 1698233400, 1698235200, 1698238800, 1698239700],
            id="select 8 time slots of 15 minutes lenght, include current quarter hour"
        ),
        pytest.param(
            "quarter_hour",
            1698227900,
            2 * ONE_HOUR_SECONDS,
            4 * ONE_HOUR_SECONDS,
            {
                # first hour
                "1698224400": IGNORED,
                "1698225300": IGNORED,
                "1698226200": EXPENSIVE,
                "1698227100": CHEEP,  # current quarert hour
                # second hour
                "1698228000": EXPENSIVE,
                "1698228900": EXPENSIVE,
                "1698229800": CHEEP,
                "1698230700": EXPENSIVE,
                # third hour
                "1698231600": CHEEP,
                "1698232500": CHEEP,
                "1698233400": CHEEP,
                "1698234300": EXPENSIVE,
                # fourth hour
                "1698235200": CHEEP,
                "1698236100": EXPENSIVE,
                "1698237000": EXPENSIVE,
                "1698237900": EXPENSIVE,
                # fifth hour
                "1698238800": CHEEP,
                "1698239700": CHEEP,
                "1698240600": EXPENSIVE,  # last before plan target
                "1698241500": IGNORED,
            },
            [1698227100, 1698229800, 1698231600, 1698232500,
             1698233400, 1698235200, 1698238800, 1698239700, 1698240600],
            id="select additional if time elapsed in current slot makes selection too short"
        ),
        pytest.param(
            "quarter_hour",
            1698226600,
            2 * ONE_HOUR_SECONDS,
            4 * ONE_HOUR_SECONDS,
            {
                # first hour
                "1698224400": IGNORED,
                "1698225300": IGNORED,
                "1698226200": EXPENSIVE,
                "1698227100": CHEEP,  # current quarert hour
                # second hour
                "1698228000": EXPENSIVE,
                "1698228900": EXPENSIVE,
                "1698229800": CHEEP,
                "1698230700": EXPENSIVE,
                # third hour
                "1698231600": CHEEP,
                "1698232500": CHEEP,
                "1698233400": CHEEP,
                "1698234300": EXPENSIVE,
                # fourth hour
                "1698235200": CHEEP,
                "1698236100": EXPENSIVE,
                "1698237000": EXPENSIVE,
                "1698237900": EXPENSIVE,
                # fifth hour
                "1698238800": EXPENSIVE,
                "1698239700": EXPENSIVE,
                "1698240600": EXPENSIVE,  # last before plan target
                "1698241500": IGNORED,
            },
            [1698227100, 1698229800, 1698231600, 1698232500, 1698233400, 1698235200, 1698238800, 1698239700],
            id="select latest if most expensive candidates have same price"
        ),
    ],
)
def test_et_get_loading_hours(granularity,
                              now_ts,
                              duration,
                              remaining_time,
                              price_list,
                              expected_loading_hours,
                              monkeypatch):
    # setup
    opt = Optional()
    opt.data.et.get.prices = price_list
    mock_et_provider_available = Mock(return_value=True)
    monkeypatch.setattr(opt, "et_provider_available", mock_et_provider_available)
    monkeypatch.setattr(
        timecheck,
        "create_timestamp",
        Mock(return_value=now_ts)
    )

    # execution
    loading_hours = opt.et_get_loading_hours(duration=duration, remaining_time=remaining_time)

    # evaluation
    assert loading_hours == expected_loading_hours
