from modules.common.component_state import TariffState
from modules.common.fault_state import FaultState
from modules.common.store import ValueStore
from modules.common.store._api import LoggingValueStore
from modules.common.store._broker import pub_to_broker
import logging


log = logging.getLogger(__name__)


class FlexibleTariffValueStoreBroker(ValueStore[TariffState]):
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
    return LoggingValueStore(FlexibleTariffValueStoreBroker())


class GridFeeValueStoreBroker(ValueStore[TariffState]):
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
    return LoggingValueStore(GridFeeValueStoreBroker())
