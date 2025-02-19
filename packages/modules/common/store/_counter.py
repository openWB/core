import logging
from operator import add

from control import data
from helpermodules import compatibility
from helpermodules.phase_mapping import convert_cp_currents_to_evu_currents
from modules.common.component_state import CounterState
from modules.common.component_type import ComponentType
from modules.common.fault_state import FaultState
from modules.common.store import ValueStore
from modules.common.store._api import LoggingValueStore
from modules.common.store._broker import pub_to_broker
from modules.common.store.ramdisk import files
from modules.common.utils.component_parser import get_component_obj_by_id

log = logging.getLogger(__name__)


class CounterValueStoreRamdisk(ValueStore[CounterState]):
    def set(self, counter_state: CounterState):
        try:
            files.evu.voltages.write(counter_state.voltages)
            if counter_state.currents:
                files.evu.currents.write(counter_state.currents)
            files.evu.powers_import.write([int(p) for p in counter_state.powers])
            files.evu.power_factors.write(counter_state.power_factors)
            files.evu.energy_import.write(counter_state.imported)
            files.evu.energy_export.write(counter_state.exported)
            files.evu.power_import.write(int(counter_state.power))
            files.evu.frequency.write(counter_state.frequency)
        except Exception as e:
            raise FaultState.from_exception(e)


class CounterValueStoreBroker(ValueStore[CounterState]):
    def __init__(self, component_num: int) -> None:
        self.num = component_num

    def set(self, counter_state: CounterState):
        self.state = counter_state

    def update(self):
        pub_to_broker("openWB/set/counter/" + str(self.num) + "/get/voltages", self.state.voltages, 2)
        if self.state.currents:
            pub_to_broker("openWB/set/counter/" + str(self.num) + "/get/currents", self.state.currents, 2)
        pub_to_broker("openWB/set/counter/" + str(self.num) + "/get/powers", self.state.powers, 2)
        pub_to_broker("openWB/set/counter/" + str(self.num) + "/get/power_factors", self.state.power_factors, 2)
        pub_to_broker("openWB/set/counter/" + str(self.num) + "/get/imported", self.state.imported)
        pub_to_broker("openWB/set/counter/" + str(self.num) + "/get/exported", self.state.exported)
        pub_to_broker("openWB/set/counter/" + str(self.num) + "/get/power", self.state.power)
        pub_to_broker("openWB/set/counter/" + str(self.num) + "/get/frequency", self.state.frequency)


class PurgeCounterState:

    def __init__(self, delegate: LoggingValueStore, add_child_values: bool = False) -> None:
        self.delegate = delegate
        self.add_child_values = add_child_values

    def set(self, state: CounterState) -> None:
        self.delegate.set(state)

    def update(self) -> None:
        state = self.calc_virtual(self.delegate.delegate.state)
        self.delegate.delegate.set(state)  # Logging in update Methode
        self.delegate.update()

    def calc_virtual(self, state: CounterState) -> CounterState:
        if self.add_child_values:
            self.currents = state.currents if state.currents else [0.0]*3
            self.power = state.power
            self.imported = state.imported
            self.exported = state.exported
            self.incomplete_currents = False

            def add_current_power(element):
                if hasattr(element, "currents") and element.currents is not None:
                    if sum(element.currents) == 0 and element.power != 0:
                        self.currents = [0, 0, 0]
                        self.incomplete_currents = True
                    else:
                        self.currents = list(map(add, self.currents, element.currents))
                else:
                    self.currents = [0, 0, 0]
                    self.incomplete_currents = True
                self.power += element.power

            def add_imported_exported(element):
                self.imported += element.imported
                self.exported += element.exported

            def add_exported(element):
                self.exported += element.exported

            counter_all = data.data.counter_all_data
            elements = counter_all.get_elements_for_downstream_calculation(self.delegate.delegate.num)
            for element in elements:
                try:
                    if element["type"] == ComponentType.CHARGEPOINT.value:
                        chargepoint = data.data.cp_data[f"cp{element['id']}"]
                        chargepoint_state = chargepoint.chargepoint_module.store.delegate.state
                        try:
                            self.currents = list(map(add,
                                                     self.currents,
                                                     convert_cp_currents_to_evu_currents(
                                                         chargepoint.data.config.phase_1,
                                                         chargepoint_state.currents)))
                        except KeyError:
                            raise KeyError("Für den virtuellen Zähler muss der Anschluss der Phasen von Ladepunkt"
                                           f" {chargepoint.data.config.name} an die Phasen des EVU Zählers "
                                           "angegeben werden.")
                        self.power += chargepoint_state.power
                        self.imported += chargepoint_state.imported
                    else:
                        component = get_component_obj_by_id(element['id'])
                        add_current_power(component.store.delegate.state)
                        if element["type"] == ComponentType.INVERTER.value:
                            add_exported(component.store.delegate.state)
                        else:
                            add_imported_exported(component.store.delegate.state)
                except Exception:
                    log.exception(f"Fehler beim Hinzufügen der Werte für Element {element}")

            if self.incomplete_currents:
                self.currents = None
            return CounterState(currents=self.currents,
                                power=self.power,
                                exported=self.exported,
                                imported=self.imported)
        else:
            return state


def get_counter_value_store(component_num: int, add_child_values: bool = False) -> PurgeCounterState:
    if compatibility.is_ramdisk_in_use():
        delegate = CounterValueStoreRamdisk()
    else:
        delegate = CounterValueStoreBroker(component_num)
    return PurgeCounterState(LoggingValueStore(delegate), add_child_values)
