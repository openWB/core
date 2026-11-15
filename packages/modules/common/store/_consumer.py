from control import data
from helpermodules.phase_handling import convert_cp_currents_to_evu_currents
from modules.common.component_state import ConsumerState
from modules.common.component_type import ComponentType
from modules.common.store import ValueStore
from modules.common.store._api import LoggingValueStore
from modules.common.store._broker import pub_to_broker
from modules.common.utils.component_parser import get_consumer_name_by_id, get_hierarchy_obj_by_id


def _to_evu_phases(state: ConsumerState, connected_phases: int, phase_1: int) -> None:
    """Die Werte eines Verbrauchers liegen wie bei den Zählern je Phase des EVU vor, nur die angeschlossenen Phasen
    ab der gewählten Phase 1 haben Werte. Module liefern die Werte in der Reihenfolge der eigenen Phasen.
    Module, die nur die Gesamtleistung liefern, bekommen von ConsumerState 230 V und 0 A/0 W auf allen drei
    Phasen, diese werden zuerst auf die angeschlossenen Phasen verteilt."""
    if any(values is not None and len(values) != 3 for values in (state.voltages, state.currents, state.powers)):
        # nutzerdefinierte Module können Listen mit anderer Länge liefern, diese bleiben unverändert
        return
    if state.voltages == [230.0]*3:
        state.voltages = [230.0 if i < connected_phases else 0.0 for i in range(3)]
    if state.power and state.currents == [0.0]*3 and (state.powers is None or state.powers == [0.0]*3):
        state.powers = [state.power / connected_phases if i < connected_phases else 0.0 for i in range(3)]
        state.currents = [power / voltage if voltage else 0.0 for power, voltage in zip(state.powers, state.voltages)]
    state.voltages = convert_cp_currents_to_evu_currents(phase_1, state.voltages)
    if state.currents is not None:
        state.currents = convert_cp_currents_to_evu_currents(phase_1, state.currents)
    if state.powers is not None:
        state.powers = convert_cp_currents_to_evu_currents(phase_1, state.powers)


class ConsumerValueStoreBroker(ValueStore[ConsumerState]):
    def __init__(self, component_num: int) -> None:
        self.num = component_num

    def set(self, state: ConsumerState) -> None:
        self.state = state
        try:
            consumer_data = data.data.consumer_data[f"consumer{self.num}"].data
            # Ein separater Zähler liefert die Werte bereits je Phase des EVU.
            if consumer_data.extra_meter is None:
                connected_phases = int(consumer_data.config.connected_phases)
                if 1 <= connected_phases <= 3:
                    _to_evu_phases(state, connected_phases, consumer_data.config.phase_1)
        except (AttributeError, KeyError, TypeError, ValueError):
            # Verbraucher (noch) nicht bekannt oder Phase 1 nicht angegeben: die Werte bleiben unverändert
            pass

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

    def update(self) -> None:
        extra_meter_id = data.data.consumer_data[f"consumer{self.delegate.delegate.num}"].data.extra_meter
        if extra_meter_id is not None:
            try:
                consumer = get_hierarchy_obj_by_id(extra_meter_id, ComponentType.COUNTER.value)
                consumer_state = consumer.store.delegate.delegate.state
                self.set(ConsumerState(
                    power=consumer_state.power,
                    imported=consumer_state.imported,
                    exported=consumer_state.exported,
                    voltages=consumer_state.voltages,
                    currents=consumer_state.currents,
                    powers=consumer_state.powers,
                ))
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
