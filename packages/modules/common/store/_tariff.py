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
        pub_to_broker("openWB/set/optional/ep/get/prices", self.sum_prices())

    def sum_prices(self):
        timestamp = timecheck.create_timestamp()
        first_timestamp = timestamp - (timestamp % 900)  # Start of current quarter hour
        # if first_timestamp != 1761127200:
        #    raise ValueError(f"Expected first timestamp to be {1761127200} but got {first_timestamp}")

        def reduce_prices(prices: Dict[str, float]) -> Dict[int, float]:
            return {int(float(k)): v for k, v in prices.items() if int(float(k)) >= first_timestamp}

        flexible_tariff_prices = reduce_prices(data.data.optional_data.data.electricity_pricing.flexible_tariff.get.prices)
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
        grid_fee_prices = {float(k): v - median_grid_fee for k, v in grid_fee_prices.items()}

        def median_delta(keys):
            """Typische Schrittweite bestimmen (Median der Deltas)"""
            if len(keys) < 2:
                return timedelta.max
            deltas = [(keys[i+1] - keys[i]) for i in range(len(keys)-1)]
            deltas.sort()
            return timedelta(seconds=deltas[len(deltas)//2])
        grid_fee_delta = median_delta(grid_fee_keys)
        electricity_tariff_delta = median_delta(flexible_tariff_keys)

        # Feinere und gröbere Auflösung bestimmen
        if grid_fee_delta < electricity_tariff_delta:
            fine_dict, coarse_dict = grid_fee_prices, flexible_tariff_prices
        else:
            fine_dict, coarse_dict = flexible_tariff_prices, grid_fee_prices
        # Intervallgrenzen für das gröbere Dict
        coarse_keys = sorted(coarse_dict.keys())
        intervalle = []
        for i, start in enumerate(coarse_keys):
            if i+1 < len(coarse_keys):
                ende = coarse_keys[i+1]
            else:
                ende = max(fine_dict.keys()) + 1
            intervalle.append((start, ende))
        # Für jeden feinen Zeitstempel das passende grobe Intervall suchen und addieren
        result = {}
        for ts_fine, preis_fine in fine_dict.items():
            coarse_value = None
            for start, ende in intervalle:
                if start <= ts_fine < ende:
                    coarse_value = coarse_dict[start]
                    break
            if coarse_value is not None:
                result[ts_fine] = preis_fine + coarse_value
        return result


def get_price_value_store() -> ValueStore[TariffState]:
    return PriceValueStore()
