from unittest.mock import Mock
import pytest
from helpermodules import timecheck
from control.optional import Optional


ONE_HOUR_SECONDS = 3600
IGNORED = 0.0001
CHEAP = 0.0002
EXPENSIVE = 0.3000


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
                "1698226200": EXPENSIVE,  # current quarter hour
                "1698227100": CHEAP,
                # second hour
                "1698228000": EXPENSIVE,
                "1698228900": EXPENSIVE,
                "1698229800": CHEAP,
                "1698230700": EXPENSIVE,
                # third hour
                "1698231600": CHEAP,
                "1698232500": CHEAP,
                "1698233400": CHEAP,
                "1698234300": EXPENSIVE,
                # fourth hour
                "1698235200": CHEAP,
                "1698236100": EXPENSIVE,
                "1698237000": EXPENSIVE,
                "1698237900": EXPENSIVE,
                # fifth hour
                "1698238800": CHEAP,
                "1698239700": CHEAP,  # last before plan target
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
                "1698227100": CHEAP,  # current quarter hour
                # second hour
                "1698228000": EXPENSIVE,
                "1698228900": EXPENSIVE,
                "1698229800": CHEAP,
                "1698230700": EXPENSIVE,
                # third hour
                "1698231600": CHEAP,
                "1698232500": CHEAP,
                "1698233400": CHEAP,
                "1698234300": EXPENSIVE,
                # fourth hour
                "1698235200": CHEAP,
                "1698236100": EXPENSIVE,
                "1698237000": EXPENSIVE,
                "1698237900": EXPENSIVE,
                # fifth hour
                "1698238800": CHEAP,
                "1698239700": CHEAP,
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
                "1698227100": CHEAP,  # current quarert hour
                # second hour
                "1698228000": EXPENSIVE,
                "1698228900": EXPENSIVE,
                "1698229800": CHEAP,
                "1698230700": EXPENSIVE,
                # third hour
                "1698231600": CHEAP,
                "1698232500": CHEAP,
                "1698233400": CHEAP,
                "1698234300": EXPENSIVE,
                # fourth hour
                "1698235200": CHEAP,
                "1698236100": EXPENSIVE,
                "1698237000": EXPENSIVE,
                "1698237900": EXPENSIVE,
                # fifth hour
                "1698238800": CHEAP,
                "1698239700": CHEAP,
                "1698240600": EXPENSIVE,
                "1698241500": EXPENSIVE,  # last before plan target
                # sixth hour
                "1698242400": IGNORED,
                "1698243300": IGNORED,
            },
            [1698227100, 1698229800, 1698231600, 1698232500,
             1698233400, 1698235200, 1698238800, 1698239700, 1698241500],
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
                "1698226200": EXPENSIVE,  # current quarter hour
                "1698227100": CHEAP,
                # second hour
                "1698228000": EXPENSIVE,
                "1698228900": EXPENSIVE,
                "1698229800": CHEAP,
                "1698230700": EXPENSIVE,
                # third hour
                "1698231600": CHEAP,
                "1698232500": CHEAP,
                "1698233400": CHEAP,
                "1698234300": EXPENSIVE,
                # fourth hour
                "1698235200": CHEAP,
                "1698236100": EXPENSIVE,
                "1698237000": EXPENSIVE,
                "1698237900": EXPENSIVE,
                # fifth hour
                "1698238800": EXPENSIVE,
                "1698239700": EXPENSIVE,
                "1698240600": EXPENSIVE,  # last before plan target
                "1698241500": EXPENSIVE,
                # sixth hour
                "1698242400": IGNORED,
                "1698243300": IGNORED,
            },
            [1698227100, 1698229800, 1698231600, 1698232500, 1698233400, 1698235200, 1698239700, 1698240600],
            id="order in time sequence equal prices"
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
                "1698226200": EXPENSIVE,  # current quarter hour
                "1698227100": .07,
                # second hour
                "1698228000": EXPENSIVE,
                "1698228900": .08,
                "1698229800": .05,
                "1698230700": .04,
                # third hour
                "1698231600": .03,
                "1698232500": .02,
                "1698233400": .01,
                "1698234300": EXPENSIVE,
                # fourth hour
                "1698235200": .04,
                "1698236100": EXPENSIVE,
                "1698237000": EXPENSIVE,
                "1698237900": EXPENSIVE,
                # fifth hour
                "1698238800": EXPENSIVE,
                "1698239700": EXPENSIVE,  # last before plan target
                "1698240600": EXPENSIVE,
                "1698241500": IGNORED,
            },
            [1698227100, 1698228900, 1698229800, 1698230700, 1698231600, 1698232500, 1698233400, 1698235200],
            id="order in time sequence reverse"
        ),
    ],
)
def test_ep_get_loading_hours(granularity,
                              now_ts,
                              duration,
                              remaining_time,
                              price_list,
                              expected_loading_hours,
                              monkeypatch):
    # setup
    opt = Optional()
    opt.data.electricity_pricing.prices = price_list
    mock_ep_provider_available = Mock(return_value=True)
    monkeypatch.setattr(opt, "ep_provider_available", mock_ep_provider_available)
    monkeypatch.setattr(
        timecheck,
        "create_timestamp",
        Mock(return_value=now_ts)
    )

    # execution
    loading_hours = opt.ep_get_loading_hours(duration=duration, remaining_time=remaining_time)

    # evaluation
    assert loading_hours == expected_loading_hours


@pytest.mark.parametrize(
    "provider_available, current_price, max_price, expected",
    [
        pytest.param(True, 0.10, 0.15, True, id="price_below_max"),
        pytest.param(True, 0.15, 0.15, True, id="price_equal_max"),
        pytest.param(True, 0.20, 0.15, False, id="price_above_max"),
        pytest.param(False, None, 0.15, True, id="provider_not_available"),
    ]
)
def test_et_charging_allowed(monkeypatch, provider_available, current_price, max_price, expected):
    opt = Optional()
    monkeypatch.setattr(opt, "ep_provider_available", Mock(return_value=provider_available))
    if provider_available:
        monkeypatch.setattr(opt, "ep_get_current_price", Mock(return_value=current_price))
    result = opt.ep_is_charging_allowed_price_threshold(max_price)
    assert result == expected


def test_et_charging_allowed_exception(monkeypatch):
    opt = Optional()
    monkeypatch.setattr(opt, "ep_provider_available", Mock(return_value=True))
    monkeypatch.setattr(opt, "ep_get_current_price", Mock(side_effect=Exception))
    result = opt.ep_is_charging_allowed_price_threshold(0.15)
    assert result is False


@pytest.mark.parametrize(
    "now_ts, provider_available, price_list, selected_hours , expected",
    [
        pytest.param(
            1698224400, False, {}, [],
            False, id="no charge if provider not available"
        ),
        pytest.param(
            1698224400, True, {
                # first hour
                "1698224400": IGNORED,
                "1698225300": IGNORED,
                "1698226200": EXPENSIVE,
                "1698227100": CHEAP,  # current quarter hour
                # second hour
                "1698228000": EXPENSIVE,
                "1698228900": EXPENSIVE,
                "1698229800": CHEAP,
                "1698230700": EXPENSIVE,
                # third hour
                "1698231600": CHEAP,
                "1698232500": CHEAP,
                "1698233400": CHEAP,
                "1698234300": EXPENSIVE,
                # fourth hour
                "1698235200": CHEAP,
                "1698236100": EXPENSIVE,
                "1698237000": EXPENSIVE,
                "1698237900": EXPENSIVE,
                # fifth hour
                "1698238800": EXPENSIVE,
                "1698239700": EXPENSIVE,
                "1698240600": EXPENSIVE,  # last before plan target
                "1698241500": IGNORED, },
            [1698227100, 1698231600,  1698232500, 1698233400, 1698235200],
            False, id="no charge if provider available but before cheapest slot"
        ),
        pytest.param(
            1698224400, True, {
                # first hour
                "1698224400": IGNORED,
                "1698225300": IGNORED,
                "1698226200": EXPENSIVE,
                "1698227100": CHEAP,  # current quarter hour
                # second hour
                "1698228000": EXPENSIVE,
                "1698228900": EXPENSIVE,
                "1698229800": CHEAP,
                "1698230700": EXPENSIVE,
                # third hour
                "1698231600": CHEAP,
                "1698232500": CHEAP,
                "1698233400": CHEAP,
                "1698234300": EXPENSIVE,
                # fourth hour
                "1698235200": CHEAP,
                "1698236100": EXPENSIVE,
                "1698237000": EXPENSIVE,
                "1698237900": EXPENSIVE,
                # fifth hour
                "1698238800": EXPENSIVE,
                "1698239700": EXPENSIVE,
                "1698240600": EXPENSIVE,  # last before plan target
                "1698241500": IGNORED, }, [],
            False, id="no charge if provider no charge times list"
        ),
        pytest.param(
            1698224400, True, {
                # second hour
                "1698228000": EXPENSIVE,
                "1698228900": EXPENSIVE,
                "1698229800": CHEAP,
                "1698230700": EXPENSIVE,
                # third hour
                "1698231600": CHEAP,
                "1698232500": CHEAP,
                "1698233400": CHEAP,
                "1698234300": EXPENSIVE,
                # fourth hour
                "1698235200": CHEAP,
                "1698236100": EXPENSIVE,
                "1698237000": EXPENSIVE,
                "1698237900": EXPENSIVE,
                # fifth hour
                "1698238800": EXPENSIVE,
                "1698239700": EXPENSIVE,
                "1698240600": EXPENSIVE,  # last before plan target
                "1698241500": IGNORED, },
            [1698227100, 1698231600,  1698232500, 1698233400, 1698235200],
            False, id="no charge if current time in expensive hour"
        ),
        pytest.param(
            1698227100, True, {
                # first hour
                "1698227100": CHEAP,  # current quarter hour
                # second hour
                "1698228000": EXPENSIVE,
                "1698228900": EXPENSIVE,
                "1698229800": CHEAP,
                "1698230700": EXPENSIVE,
                # third hour
                "1698231600": CHEAP,
                "1698232500": CHEAP,
                "1698233400": CHEAP,
                "1698234300": EXPENSIVE,
                # fourth hour
                "1698235200": CHEAP,
                "1698236100": EXPENSIVE,
                "1698237000": EXPENSIVE,
                "1698237900": EXPENSIVE,
                # fifth hour
                "1698238800": EXPENSIVE,
                "1698239700": EXPENSIVE,
                "1698240600": EXPENSIVE,  # last before plan target
                "1698241500": IGNORED, },
            [1698227100, 1698231600,  1698232500, 1698233400, 1698235200],
            True, id="charge if provider available and matching time slot start"
        ),
        pytest.param(
            1698227100, True, {
                # first hour
                "1698227100": IGNORED,  # current quarter hour
                # second hour
                "1698228000": IGNORED,
                "1698228900": IGNORED,
                "1698229800": IGNORED,
                "1698230700": IGNORED,
                # third hour
                "1698231600": IGNORED,
                "1698232500": IGNORED,
                "1698233400": IGNORED,
                "1698234300": IGNORED,
                # fourth hour
                "1698235200": IGNORED,
                "1698236100": IGNORED,
                "1698237000": IGNORED,
                "1698237900": IGNORED,
                # fifth hour
                "1698238800": IGNORED,
                "1698239700": IGNORED,
                "1698240600": IGNORED,  # last before plan target
                "1698241500": IGNORED, },
            [1698227100, 1698231600,  1698232500, 1698233400, 1698235200],
            True, id="charge if provider available and matching time slot start"
        ),
    ]
)
def test_et_charging_available(now_ts, provider_available, price_list, selected_hours, expected, monkeypatch):
    monkeypatch.setattr(
        timecheck,
        "create_timestamp",
        Mock(return_value=now_ts)
    )
    opt = Optional()
    opt.data.electricity_pricing.prices = price_list
    monkeypatch.setattr(opt, "ep_provider_available", Mock(return_value=provider_available))
    result = opt.ep_is_charging_allowed_hours_list(selected_hours)
    assert result == expected


def test_et_charging_available_exception(monkeypatch):
    opt = Optional()
    monkeypatch.setattr(opt, "ep_provider_available", Mock(return_value=True))

    opt.data.electricity_pricing.prices = {}  # empty prices list raises exception
    result = opt.ep_is_charging_allowed_hours_list([])
    assert result is False


@pytest.mark.parametrize(
    "prices, next_query_time, current_timestamp, expected",
    [
        pytest.param(
            {}, None, 1698224400, True,
            id="update_required_when_no_prices"
        ),
        pytest.param(
            {"1698224400": 0.1, "1698228000": 0.2}, None, 1698224400, False,
            id="no_update_required_when_prices_available_and_recent"
        ),
        pytest.param(
            {"1698224400": 0.1, "1698228000": 0.2}, 1698310800, 1698224400, False,
            id="no_update_required_when_next_query_time_not_reached"
        ),
        pytest.param(
            {"1698224400": 0.1, "1698228000": 0.2}, 1698224000, 1698310800, True,
            id="update_required_when_next_query_time_passed"
        ),
        pytest.param(
            {"1609459200": 0.1, "1609462800": 0.2}, None, 1698224400, True,
            id="update_required_when_prices_from_yesterday"
        ),
    ]
)
def test_et_price_update_required(monkeypatch, prices, next_query_time, current_timestamp, expected):
    # setup
    opt = Optional()
    opt.data.electricity_pricing.get.prices = prices
    opt.data.electricity_pricing.get.next_query_time = next_query_time

    monkeypatch.setattr(timecheck, "create_timestamp", Mock(return_value=current_timestamp))

    # execution
    result = opt.et_price_update_required()

    # evaluation
    assert result == expected
