from datetime import timedelta
from control import data
from modules.common.component_state import TariffState
from modules.common.fault_state import FaultState
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
        try:
            prices = self.state.prices
            pub_to_broker("openWB/set/optional/ep/flexible_tariff/get/prices", prices)
            log.debug(f"published prices list to MQTT having {len(prices)} entries")
        except Exception as e:
            raise FaultState.from_exception(e)


def get_flexible_tariff_value_store() -> ValueStore[TariffState]:
    return LoggingValueStore(FlexibleTariffValueStore())


class GridFeeValueStore(ValueStore[TariffState]):
    def __init__(self):
        pass

    def set(self, state: TariffState) -> None:
        self.state = state

    def update(self):
        try:
            prices = self.state.prices
            pub_to_broker("openWB/set/optional/ep/grid_fee/get/prices", prices)
            log.debug(f"published grid tariff prices list to MQTT having {len(prices)} entries")
        except Exception as e:
            raise FaultState.from_exception(e)


def get_grid_fee_value_store() -> ValueStore[TariffState]:
    return LoggingValueStore(GridFeeValueStore())


class PriceValueStore(ValueStore[TariffState]):
    def __init__(self):
        pass

    def update(self):
        try:
            pub_to_broker("openWB/set/optional/ep/get/prices", self.sum_prices())
        except Exception as e:
            raise FaultState.from_exception(e)

    def sum_prices(self):
        flexible_tariff_prices = data.data.optional_data.data.electricity_pricing.flexible_tariff.get.prices
        grid_fee_prices = data.data.optional_data.data.electricity_pricing.grid_fee.get.prices
        flexible_tariff_prices = {float(k): v for k, v in flexible_tariff_prices.items()}
        grid_fee_prices = {float(k): v for k, v in grid_fee_prices.items()}
        if flexible_tariff_prices is None and grid_fee_prices is not None:
            return grid_fee_prices
        if grid_fee_prices is None and flexible_tariff_prices is not None:
            return flexible_tariff_prices

        grid_fee_keys = sorted(grid_fee_prices.keys())
        flexible_tariff_keys = sorted(flexible_tariff_prices.keys())

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
            if coarse_value is None:
                raise ValueError(f"Kein passendes Intervall für {ts_fine}")
            result[ts_fine] = preis_fine + coarse_value
        return result


def get_price_value_store() -> ValueStore[TariffState]:
    return PriceValueStore()
