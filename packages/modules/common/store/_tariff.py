from datetime import timedelta, datetime
from typing import Dict
from helpermodules import timecheck
from control import data
from modules.common.component_state import TariffState
from modules.common.store import ValueStore
from modules.common.store._api import LoggingValueStore
from modules.common.store._broker import pub_to_broker
import logging


log = logging.getLogger(__name__)


class FlexibleTariffValueStore(ValueStore[TariffState]):
    def __init__(self):
        pass

    def set(self, state: TariffState) -> None:
        self.state = state

    def update(self):
        prices = self.state.prices
        pub_to_broker("openWB/set/optional/ep/flexible_tariff/get/prices", prices)
        log.debug(f"published prices list to MQTT having {len(prices)} entries")


def get_flexible_tariff_value_store() -> ValueStore[TariffState]:
    return LoggingValueStore(FlexibleTariffValueStore())


class GridFeeValueStore(ValueStore[TariffState]):
    def __init__(self):
        pass

    def set(self, state: TariffState) -> None:
        self.state = state

    def update(self):
        prices = self.state.prices
        pub_to_broker("openWB/set/optional/ep/grid_fee/get/prices", prices)
        log.debug(f"published grid tariff prices list to MQTT having {len(prices)} entries")


def get_grid_fee_value_store() -> ValueStore[TariffState]:
    return LoggingValueStore(GridFeeValueStore())


class PriceValueStore(ValueStore[TariffState]):
    def __init__(self):
        pass

    def update(self):
        log.debug("Updating combined prices for flexible tariff and grid fee")
        pub_to_broker("openWB/set/optional/ep/get/prices", self.sum_prices())

    def sum_prices(self):
        timestamp = timecheck.create_timestamp()
        first_timestamp = timestamp - (timestamp % 900)  # Start of current quarter hour
        log.debug(f"Summing prices for timestamp {timestamp} (first timestamp: {first_timestamp})")

        def median_delta(keys):
            """Typische Schrittweite bestimmen (Median der Deltas)"""
            if len(keys) < 2:
                return timedelta.max
            deltas = [(keys[i+1] - keys[i]) for i in range(len(keys)-1)]
            deltas.sort()
            return timedelta(seconds=deltas[len(deltas)//2])

        def _get_value_at_or_before(d: Dict[int, float], ts_key: int) -> float:
            """Return value for the greatest key <= ts_key, or the earliest value if none."""
            keys = [k for k in d.keys() if k <= ts_key]
            if keys:
                key = max(keys)
            else:
                key = min(d.keys())
            return d[key]

        def reduce_prices(prices: Dict[str, float]) -> Dict[int, float]:
            prices = {int(float(k)): v for k, v in prices.items() if int(float(k)) >= first_timestamp}
            if (len(prices) > 0):
                median_delta_seconds = median_delta(sorted(int(float(k)) for k in prices.keys())).total_seconds()
                if median_delta_seconds > 900:
                    # Wenn die typische Schrittweite größer als 15 Minuten ist, annehmen,
                    # dass es sich um unregelmäßige Preise handelt
                    last_timestamp = max(int(float(k)) for k in prices.keys())
                    target_timestamp = (
                        datetime.fromtimestamp(last_timestamp).replace(second=59, microsecond=0).timestamp())
                    for ts in range(int(first_timestamp), int(target_timestamp), 900):
                        if ts not in prices:
                            prices[ts] = _get_value_at_or_before(prices, ts)
            return prices

        flexible_tariff_prices = reduce_prices(
            data.data.optional_data.data.electricity_pricing.flexible_tariff.get.prices)
        if len(flexible_tariff_prices) == 0 and data.data.optional_data.flexible_tariff_module is not None:
            raise ValueError("Keine Preise für konfigurierten dynamischen Stromtarif vorhanden.")
        grid_fee_prices = reduce_prices(data.data.optional_data.data.electricity_pricing.grid_fee.get.prices)
        if len(grid_fee_prices) == 0 and data.data.optional_data.grid_fee_module is not None:
            raise ValueError("Keine Preise für konfigurierten Netzentgelttarif vorhanden.")
        flexible_tariff_prices = {int(float(k)): v for k, v in flexible_tariff_prices.items()}
        grid_fee_prices = {int(float(k)): v for k, v in grid_fee_prices.items()}
        if len(flexible_tariff_prices) == 0 and len(grid_fee_prices) > 0:
            return grid_fee_prices
        if len(grid_fee_prices) == 0 and len(flexible_tariff_prices) > 0:
            return flexible_tariff_prices

        flexible_tariff_keys = sorted(flexible_tariff_prices.keys())
        grid_fee_keys = sorted(grid_fee_prices.keys())
        # Get distinct grid_fee_prices values, sort and take the middle one
        distinct_grid_fee_values = sorted(set(grid_fee_prices.values()))
        median_grid_fee = (
            distinct_grid_fee_values[len(distinct_grid_fee_values) // 2]
            if distinct_grid_fee_values else 0)
        grid_fee_prices = {int(float(k)): v - median_grid_fee for k, v in grid_fee_prices.items()}

        median_delta_seconds_grid = median_delta(
            sorted(int(float(k)) for k in grid_fee_prices.keys())).total_seconds()
        median_delta_seconds_flexible = median_delta(
            sorted(int(float(k)) for k in flexible_tariff_prices.keys())).total_seconds()

        result = {}
        def _get_value_from_keys(d: Dict[int, float], keys_list: list, ts_key: int) -> float:
            keys = [k for k in keys_list if k <= ts_key]
            if keys:
                key = max(keys)
            else:
                key = min(keys_list)
            return d[key]

        for ts in (flexible_tariff_keys
                   if median_delta_seconds_flexible < median_delta_seconds_grid
                   else grid_fee_keys):
            result[ts] = (_get_value_from_keys(flexible_tariff_prices, flexible_tariff_keys, ts) +
                          _get_value_from_keys(grid_fee_prices, grid_fee_keys, ts))
        return result


def get_price_value_store() -> ValueStore[TariffState]:
    return PriceValueStore()
