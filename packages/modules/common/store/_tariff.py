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

        def __get_value_at_or_before(d: Dict[int, float], ts_key: int) -> float:
            """Return value for the greatest key <= ts_key, or the earliest value if none."""
            keys = [k for k in d.keys() if k <= ts_key]
            if keys:
                key = max(keys)
            else:
                key = min(d.keys())
            return d[key]

        def __reduce_prices(prices: Dict[str, float]) -> Dict[int, float]:
            return {int(float(k)): v for k, v in prices.items() if int(float(k)) >= first_timestamp}

        def __get_default_grid_fee_price(prices: Dict[str, float]) -> float:
            if (hasattr(data.data.optional_data.grid_fee_module.config, "default_price") and
                    data.data.optional_data.grid_fee_module.config.default_price is not None):
                print("Using default grid fee price from configuration: " +
                      f"{data.data.optional_data.grid_fee_module.config.default_price}")
                return data.data.optional_data.grid_fee_module.config.default_price
            else:
                # Fallback: Median der vorhandenen Netzentgelte wird
                # als Schätzung für das Standard-Netzentgelt verwenden
                distinct_grid_fee_values = sorted(set(prices.values()))
                return (
                    distinct_grid_fee_values[len(distinct_grid_fee_values) // 2]
                    if distinct_grid_fee_values else 0)

        def __normalize_grid_fee_prices(grid_fee_prices: Dict[int, float], max_timestamp: int) -> Dict[int, float]:
            '''
              Normalisiert die Netzentgelte.
              Dies ist notwendig, da Nettzentgelte die Preisen einiger Stromanbieter
              bereits ein festes Netzentgeld enthalten.
            '''
            grid_fee_prices = __reduce_prices(grid_fee_prices)
            grid_fee_prices = {int(float(k)): v for k, v in grid_fee_prices.items() if int(float(k)) <= max_timestamp}

            if (hasattr(data.data.optional_data.flexible_tariff_module.config, "includes_grid_fee")
                    and data.data.optional_data.flexible_tariff_module.config.includes_grid_fee is False):
                return grid_fee_prices
            else:
                #  Bei flexiblen Tarifen, die das Netzentgeln _nicht_ enthalten,
                #  muss "includes_grid_fee" explizit auf False gesetzt werden.
                return {int(float(k)): v - __get_default_grid_fee_price(grid_fee_prices)
                        for k, v in grid_fee_prices.items()}

        def __sum_of_tariff_and_grid_fee(
                flexible_tariff_prices: Dict[int, float],
                grid_fee_prices: Dict[int, float]
                ) -> Dict[int, float]:
            grid_fee_prices = __normalize_grid_fee_prices(grid_fee_prices, max(flexible_tariff_prices.keys()))
            timestamps = sorted(list(set(flexible_tariff_prices.keys()) | set(grid_fee_prices.keys())))
            return {ts: (__get_value_at_or_before(flexible_tariff_prices, ts) +
                         __get_value_at_or_before(grid_fee_prices, ts))
                    for ts in timestamps if ts <= max(flexible_tariff_prices.keys())}

        optional_data = data.data.optional_data
        electricity_pricing = optional_data.data.electricity_pricing
        flexible_tariff_prices = {int(float(k)): v for k, v
                                  in electricity_pricing.flexible_tariff.get.prices.items()}
        grid_fee_prices = {int(float(k)): v for k, v
                           in electricity_pricing.grid_fee.get.prices.items()}

        flexible_tariff_prices = __reduce_prices(flexible_tariff_prices)
        if len(grid_fee_prices) == 0 and len(flexible_tariff_prices) > 0:
            return flexible_tariff_prices

        if len(flexible_tariff_prices) == 0 and len(grid_fee_prices) > 0:
            return __reduce_prices(grid_fee_prices)

        return __sum_of_tariff_and_grid_fee(flexible_tariff_prices, grid_fee_prices)


def get_price_value_store() -> ValueStore[TariffState]:
    return PriceValueStore()
