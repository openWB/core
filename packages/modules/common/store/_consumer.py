from control import data
from modules.common.component_state import ConsumerState
from modules.common.component_type import ComponentType
from modules.common.store import ValueStore
from modules.common.store._api import LoggingValueStore
from modules.common.store._broker import pub_to_broker
from modules.common.utils.component_parser import get_hierarchy_obj_by_id


class ConsumerValueStoreBroker(ValueStore[ConsumerState]):
    def __init__(self, component_num: int) -> None:
        self.num = component_num

    def set(self, state: ConsumerState) -> None:
        self.state = state

    def zero_power_on_sustained_error(self) -> None:
        self.state.power = 0

    def update(self) -> None:
        if self.state.currents is not None:
            pub_to_broker(f"openWB/set/consumer/{self.num}/get/currents", self.state.currents, 2)
        if self.state.powers is not None:
            pub_to_broker(f"openWB/set/consumer/{self.num}/get/powers", self.state.powers, 2)
        if self.state.power is not None:
            pub_to_broker(f"openWB/set/consumer/{self.num}/get/power", self.state.power, 2)
        if self.state.set_power is not None:
            pub_to_broker(f"openWB/set/consumer/{self.num}/get/set_power", self.state.set_power, 2)
        if self.state.state is not None:
            pub_to_broker(f"openWB/set/consumer/{self.num}/get/state", self.state.state, 2)
        pub_to_broker(f"openWB/set/consumer/{self.num}/get/voltages", self.state.voltages, 2)
        if self.state.imported is not None and self.state.exported is not None:
            pub_to_broker(f"openWB/set/consumer/{self.num}/get/imported", self.state.imported, 2)
            pub_to_broker(f"openWB/set/consumer/{self.num}/get/exported", self.state.exported, 2)
        if self.state.temperatures is not None:
            pub_to_broker(f"openWB/set/consumer/{self.num}/get/temperatures", self.state.temperatures)


class PurgeConsumerState(ValueStore[ConsumerState]):
    def __init__(self, delegate: LoggingValueStore[ConsumerState]) -> None:
        self.delegate = delegate

    def set(self, state: ConsumerState) -> None:
        self.delegate.set(state)

    def zero_power_on_sustained_error(self) -> None:
        self.delegate.zero_power_on_sustained_error()

    def update(self) -> None:
        extra_meter_id = data.data.consumer_data[f"consumer{self.delegate.delegate.num}"].data.extra_meter
        if extra_meter_id is not None:
            try:
                counter = get_hierarchy_obj_by_id(extra_meter_id, ComponentType.COUNTER.value)
                counter_state = counter.store.delegate.delegate.state
                # Leistung kommt vom Zähler, nicht vom Verbraucher - dessen Fehlerzustand zählt hier nicht.
                power = 0 if counter.fault_state.error_duration_exceeded() else counter_state.power
                self.set(ConsumerState(
                    power=power,
                    imported=counter_state.imported,
                    exported=counter_state.exported,
                    voltages=counter_state.voltages,
                    currents=counter_state.currents,
                    powers=counter_state.powers,
                ))
            except Exception:
                raise Exception(f"Fehler beim Auslesen des Verbrauchszählers {extra_meter_id} "
                                f"für Verbraucher {self.delegate.delegate.num}")
        self.delegate.update()


def get_consumer_value_store(component_num: int) -> ValueStore[ConsumerState]:
    return PurgeConsumerState(LoggingValueStore(ConsumerValueStoreBroker(component_num)))
