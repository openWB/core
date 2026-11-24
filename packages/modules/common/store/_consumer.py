from control import data
from modules.common.component_state import ConsumerState
from modules.common.component_type import ComponentType
from modules.common.store import ValueStore
from modules.common.store._api import LoggingValueStore
from modules.common.store._broker import pub_to_broker
from modules.common.utils.component_parser import get_consumer_name_by_id, get_hierarchy_obj_by_id


class ConsumerValueStoreBroker(ValueStore[ConsumerState]):
    def __init__(self, component_num: int) -> None:
        self.num = component_num

    def set(self, state: ConsumerState) -> None:
        try:
            consumer_data = data.data.consumer_data[f"consumer{self.num}"].data
            # Ein separater Zähler liefert die Werte je Phase selbst.
            if consumer_data.extra_meter is None:
                state.distribute_total_power(int(consumer_data.config.connected_phases))
        except (AttributeError, KeyError, TypeError, ValueError):
            # Verbraucher (noch) nicht bekannt: die Werte bleiben unverändert
            pass
        self.state = state

    def zero_power_on_sustained_error(self) -> None:
        if hasattr(self, "state"):
            self.state.power = 0
        else:
            self.state = ConsumerState(power=0)

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
        if self.state.rfid is not None:
            pub_to_broker(f"openWB/set/consumer/{self.num}/get/rfid", self.state.rfid)
        if self.state.rfid_timestamp is not None:
            pub_to_broker(f"openWB/set/consumer/{self.num}/get/rfid_timestamp", self.state.rfid_timestamp)


class PurgeConsumerState(ValueStore[ConsumerState]):
    def __init__(self, delegate: LoggingValueStore[ConsumerState]) -> None:
        self.delegate = delegate

    def set(self, state: ConsumerState) -> None:
        self.delegate.set(state)

    def zero_power_on_sustained_error(self) -> None:
        self.delegate.zero_power_on_sustained_error()

    def update(self) -> None:
        consumer = data.data.consumer_data[f"consumer{self.delegate.delegate.num}"]
        extra_meter_id = consumer.data.extra_meter
        if extra_meter_id is not None:
            try:
                counter = get_hierarchy_obj_by_id(extra_meter_id, ComponentType.COUNTER.value)
                counter_state = counter.store.delegate.delegate.state
                self.set(ConsumerState(
                    power=counter_state.power,
                    imported=counter_state.imported,
                    exported=counter_state.exported,
                    voltages=counter_state.voltages,
                    currents=counter_state.currents,
                    powers=counter_state.powers,
                ))
                if consumer.module.fault_state.fault_state == 0:
                    consumer.module.fault_state.from_exception(counter.fault_state)
                    if consumer.module.fault_state.fault_state != 0:
                        consumer.module.fault_state.fault_str = (
                            f"Verknüpfter Zähler: {counter.fault_state.fault_str}")
            except ValueError:
                raise Exception(
                    f"Zähler {extra_meter_id} für die separate Leistungsmessung von Verbraucher "
                    f"{get_consumer_name_by_id(self.delegate.delegate.num)} ist im Fehlerzustand oder gelöscht worden.")
            except Exception:
                raise Exception(f"Fehler beim Auslesen des Verbrauchszählers {extra_meter_id} "
                                f"für Verbraucher {self.delegate.delegate.num}")
        self.delegate.update()


def get_consumer_value_store(component_num: int) -> ValueStore[ConsumerState]:
    return PurgeConsumerState(LoggingValueStore(ConsumerValueStoreBroker(component_num)))
