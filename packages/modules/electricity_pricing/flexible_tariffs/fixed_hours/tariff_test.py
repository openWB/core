#!/usr/bin/env python3
import datetime
import time
import pytest

from modules.electricity_pricing.flexible_tariffs.fixed_hours.tariff import (
    _to_time,
    _to_date,
    _validate_tariff_times,
    _fetch,
    create_electricity_tariff,
)
from modules.electricity_pricing.flexible_tariffs.fixed_hours.config import (
    FixedHoursTariff,
    FixedHoursTariffConfiguration,
)
from modules.common.component_state import TariffState


class TestToTime:
    """Test _to_time function"""

    @pytest.mark.parametrize(
        "time_str,expected",
        [
            pytest.param("14:30", datetime.time(14, 30), id="14:30"),
            pytest.param("00:00", datetime.time(0, 0), id="midnight"),
            pytest.param("24:00", datetime.time(23, 59, 59), id="24:00"),
            pytest.param("08:00", datetime.time(8, 0), id="08:00"),
            pytest.param("18:45", datetime.time(18, 45), id="18:45"),
            pytest.param("23:59", datetime.time(23, 59), id="23:59"),
        ],
    )
    def test_to_time_conversion(self, time_str, expected):
        """Test conversion of various time strings"""
        result = _to_time(time_str)
        assert result == expected


class TestToDate:
    """Test _to_date function"""

    @pytest.mark.parametrize(
        "date_str,time_slot,expected",
        [
            pytest.param(
                "15-06",
                datetime.datetime(2025, 6, 15, 12, 0),
                datetime.date(2025, 6, 15),
                id="normal_date",
            ),
            pytest.param(
                "01-01",
                datetime.datetime(2025, 1, 15, 12, 0),
                datetime.date(2025, 1, 1),
                id="new_year",
            ),
            pytest.param(
                "31-03",
                datetime.datetime(2025, 3, 31, 12, 0),
                datetime.date(2025, 3, 31),
                id="month_end",
            ),
            pytest.param(
                "28-02",
                datetime.datetime(2025, 2, 28, 12, 0),
                datetime.date(2025, 2, 28),
                id="feb_28",
            ),
            pytest.param(
                "25-12",
                datetime.datetime(2025, 12, 25, 12, 0),
                datetime.date(2025, 12, 25),
                id="christmas",
            ),
        ],
    )
    def test_to_date_conversion(self, date_str, time_slot, expected):
        """Test conversion of various date strings"""
        result = _to_date(date_str, time_slot)
        assert result == expected


class TestValidateTariffTimes:
    """Test _validate_tariff_times function"""

    @pytest.mark.parametrize(
        "tariffs,should_pass",
        [
            # Non-overlapping times
            pytest.param(
                [
                    {
                        "name": "tariff1",
                        "price": 100,
                        "active_times": {
                            "dates": [("01-01", "31-12")],
                            "times": [("08:00", "12:00")],
                        },
                    },
                    {
                        "name": "tariff2",
                        "price": 200,
                        "active_times": {
                            "dates": [("01-01", "31-12")],
                            "times": [("14:00", "18:00")],
                        },
                    },
                ],
                True,
                id="non_overlapping",
            ),
            # Adjacent times
            pytest.param(
                [
                    {
                        "name": "tariff1",
                        "price": 100,
                        "active_times": {
                            "dates": [("01-01", "31-12")],
                            "times": [("08:00", "12:00")],
                        },
                    },
                    {
                        "name": "tariff2",
                        "price": 200,
                        "active_times": {
                            "dates": [("01-01", "31-12")],
                            "times": [("12:00", "14:00")],
                        },
                    },
                ],
                True,
                id="adjacent_times",
            ),
            # Empty tariffs
            pytest.param([], True, id="empty_tariffs"),
        ],
    )
    def test_validate_tariff_times(self, tariffs, should_pass):
        """Test validation of tariff time configurations"""
        config = FixedHoursTariffConfiguration(default_price=1000, tariffs=tariffs)

        if should_pass:
            _validate_tariff_times(config)
        else:
            with pytest.raises(ValueError, match="Overlapping time window detected"):
                _validate_tariff_times(config)


class TestFetch:
    """Test _fetch function"""

    @pytest.mark.parametrize(
        "default_price,tariffs,expected_price",
        [
            # No tariffs, use default price
            pytest.param(1500, [], 1.5, id="no_tariffs"),
            # All-day tariff
            pytest.param(
                1500,
                [
                    {
                        "name": "all_day_tariff",
                        "price": 2000,
                        "active_times": {
                            "dates": [("01-01", "31-12")],
                            "times": [("00:00", "24:00")],
                        },
                    }
                ],
                2.0,
                id="all_day_tariff",
            ),
            # Tariff that matches all times
            pytest.param(
                1500,
                [
                    {
                        "name": "tariff1",
                        "price": 2500,
                        "active_times": {
                            "dates": [("01-01", "31-12")],
                            "times": [("00:00", "24:00")],
                        },
                    }
                ],
                2.5,
                id="full_day_tariff",
            ),
            # Very low price
            pytest.param(500, [], 0.5, id="low_price"),
            # Very high price
            pytest.param(5000, [], 5.0, id="high_price"),
        ],
    )
    def test_fetch_price_configurations(self, default_price, tariffs, expected_price):
        """Test fetch with various price configurations"""
        config = FixedHoursTariffConfiguration(
            default_price=default_price, tariffs=tariffs
        )

        result = _fetch(config)

        assert isinstance(result, TariffState)
        assert len(result.prices) > 0
        for price in result.prices.values():
            assert isinstance(price, float)
            assert price == expected_price

    @pytest.mark.parametrize(
        "default_price,tariffs",
        [
            # No tariffs
            pytest.param(1500, [], id="no_tariffs"),
            # All-day tariff
            pytest.param(
                1500,
                [
                    {
                        "name": "all_day_tariff",
                        "price": 2000,
                        "active_times": {
                            "dates": [("01-01", "31-12")],
                            "times": [("00:00", "24:00")],
                        },
                    }
                ],
                id="all_day_tariff",
            ),
        ],
    )
    def test_fetch_first_entry_starts_with_current_quarter_hour(
        self, default_price, tariffs
    ):
        """Test that the first entry in the prices map starts with the current quarter hour"""
        config = FixedHoursTariffConfiguration(
            default_price=default_price, tariffs=tariffs
        )

        result = _fetch(config)

        assert isinstance(result, TariffState)
        assert len(result.prices) > 0

        # Get the first timestamp (smallest key)
        first_timestamp_str = min(result.prices.keys())
        first_timestamp = int(float(first_timestamp_str))

        # Get current time rounded to the current hour
        current_time = datetime.datetime.now().replace(minute=0, second=0, microsecond=0)
        expected_timestamp = int(time.mktime(current_time.timetuple()))

        # The first entry should be at or after the current hour
        assert first_timestamp >= expected_timestamp


class TestCreateElectricityTariff:
    """Test create_electricity_tariff function"""

    @pytest.mark.parametrize(
        "default_price,tariffs,expected_price",
        [
            # No tariffs, use default
            pytest.param(1500, [], 1.5, id="no_tariffs"),
            # With all-day tariff
            pytest.param(
                1500,
                [
                    {
                        "name": "test_tariff",
                        "price": 2500,
                        "active_times": {
                            "dates": [("01-01", "31-12")],
                            "times": [("00:00", "24:00")],
                        },
                    }
                ],
                2.5,
                id="all_day_tariff",
            ),
            # Another tariff configuration
            pytest.param(
                2000,
                [
                    {
                        "name": "premium_tariff",
                        "price": 3500,
                        "active_times": {
                            "dates": [("01-01", "31-12")],
                            "times": [("00:00", "24:00")],
                        },
                    }
                ],
                3.5,
                id="premium_tariff",
            ),
        ],
    )
    def test_create_electricity_tariff_updater(
        self, default_price, tariffs, expected_price
    ):
        """Test the create_electricity_tariff updater with various configurations"""
        config = FixedHoursTariff(
            configuration=FixedHoursTariffConfiguration(
                default_price=default_price, tariffs=tariffs
            )
        )

        updater = create_electricity_tariff(config)

        assert callable(updater)
        result = updater()

        assert isinstance(result, TariffState)
        assert len(result.prices) > 0
        for price in result.prices.values():
            assert price == expected_price
