from modules.common.component_state import TariffState
from modules.common.fault_state import FaultState
from modules.common.store import ValueStore
from modules.common.store._api import LoggingValueStore
from modules.common.store._broker import pub_to_broker


class TariffValueStoreBroker(ValueStore[TariffState]):
    def __init__(self):
        pass

    def set(self, state: TariffState) -> None:
        self.state = state

    def update(self):
        try:
            pub_to_broker("openWB/set/optional/et/get/prices", self.state.prices)
        except Exception as e:
            raise FaultState.from_exception(e)


def get_electricity_tariff_value_store() -> ValueStore[TariffState]:
    return LoggingValueStore(TariffValueStoreBroker())
