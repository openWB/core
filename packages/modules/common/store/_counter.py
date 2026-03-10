import logging
from operator import add
from typing import Dict, Optional

from control import data
from helpermodules import compatibility
from helpermodules.phase_handling import convert_cp_currents_to_evu_currents
from modules.common.component_state import CounterState
from modules.common.component_type import ComponentType
from modules.common.simcount._simcounter import SimCounter
from modules.common.store import ValueStore
from modules.common.store._api import LoggingValueStore
from modules.common.store._broker import pub_to_broker
from modules.common.store.ramdisk import files
from modules.common.utils.component_parser import get_component_obj_by_id

log = logging.getLogger(__name__)


class CounterValueStoreRamdisk(ValueStore[CounterState]):
    def set(self, counter_state: CounterState):
        files.evu.voltages.write(counter_state.voltages)
        if counter_state.currents:
            files.evu.currents.write(counter_state.currents)
        files.evu.powers_import.write([int(p) for p in counter_state.powers])
        files.evu.power_factors.write(counter_state.power_factors)
        files.evu.energy_import.write(counter_state.imported)
        files.evu.energy_export.write(counter_state.exported)
        files.evu.power_import.write(int(counter_state.power))
        files.evu.frequency.write(counter_state.frequency)


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
        if self.state.serial_number is not None:
            pub_to_broker("openWB/set/counter/" + str(self.num) + "/get/serial_number", self.state.serial_number)


class PurgeCounterState:

    def __init__(self,
                 delegate: LoggingValueStore,
                 add_child_values: bool = False,
                 simcounter: Optional[SimCounter] = None) -> None:
        self.delegate = delegate
        self.add_child_values = add_child_values
        self.sim_counter = simcounter

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
            self.imported = state.imported if state.imported else 0
            self.exported = state.exported if state.exported else 0
            self.incomplete_currents = False
            counter_all = data.data.counter_all_data
            elements = counter_all.get_elements_for_downstream_calculation(self.delegate.delegate.num)
            if len(elements) == 0:
                return self.calc_uncounted_consumption()
            else:
                return self.calc_consumers(elements)
        else:
            return state

    def _add_values(self, element, calc_imported_exported: bool):
        if hasattr(element, "currents") and element.currents is not None:
            if sum(element.currents) == 0 and element.power != 0:
                self.currents = [0, 0, 0]
                self.incomplete_currents = True
            else:
                self.currents = list(map(add, self.currents, element.currents))
        else:
            self.currents = [0, 0, 0]
            self.incomplete_currents = True
        if calc_imported_exported:
            if hasattr(element, "imported") and element.imported is not None:
                self.imported += element.imported
            if hasattr(element, "exported") and element.exported is not None:
                self.exported += element.exported
        self.power += element.power

    def calc_consumers(self, elements: Dict, calc_imported_exported: bool = False) -> CounterState:
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
                    if calc_imported_exported:
                        self.imported += chargepoint_state.imported
                        self.exported += chargepoint_state.exported
                else:
                    component = get_component_obj_by_id(element['id'])
                    self._add_values(component.store.delegate.delegate.state, calc_imported_exported)
            except Exception:
                log.exception(f"Fehler beim Hinzufügen der Werte für Element {element}")

        if calc_imported_exported is False or self.imported is None or self.exported is None:
            if self.imported is None and calc_imported_exported:
                log.debug("Mind eine Komponente liefert keinen Zählestand für den Bezug, berechne Zählerstände")
            if self.exported is None and calc_imported_exported:
                log.debug("Mind eine Komponente liefert keinen Zählestand für die Einspeisung, berechne Zählerstände")
            self.imported, self.exported = self.sim_counter.sim_count(self.power)
        if self.incomplete_currents:
            self.currents = None
        return CounterState(currents=self.currents,
                            power=self.power,
                            exported=self.exported,
                            imported=self.imported)

    def calc_uncounted_consumption(self) -> CounterState:
        """Berechnet den nicht-gezählten Verbrauch für einen virtuellen Zähler.
        Dazu wird der Zählerstand des übergeordneten Zählers herangezogen und davon die
        Werte aller anderen untergeordneten Komponenten abgezogen."""
        parent_id = data.data.counter_all_data.get_entry_of_parent(self.delegate.delegate.num)["id"]
        parent_component = get_component_obj_by_id(parent_id)
        if "counter" not in parent_component.component_config.type:
            raise Exception("Die übergeordnete Komponente des virtuellen Zählers muss ein Zähler sein.")
        if parent_component.store.add_child_values:
            raise Exception("Der übergeordnete Zähler des virtuellen Zählers darf nicht "
                            "auch ein virtueller Zähler sein.")
        elements = data.data.counter_all_data.get_elements_for_downstream_calculation(parent_id)
        # entferne den eigenen Zähler aus der Liste
        elements = [el for el in elements if el["id"] != self.delegate.delegate.num]
        self.calc_consumers(elements, calc_imported_exported=True)
        log.debug(f"Erfasster Verbrauch virtueller Zähler {self.delegate.delegate.num}: "
                  f"{self.currents}A, {self.power}W, {self.exported}Wh, {self.imported}Wh")
        parent_counter_get = data.data.counter_data[f"counter{parent_id}"].data.get
        return CounterState(
            currents=[parent_counter_get.currents[i] - self.currents[i]
                      for i in range(0, 3)] if self.currents is not None else None,
            power=parent_counter_get.power - self.power,
            exported=0,
            imported=(parent_counter_get.imported + self.exported - self.imported -
                      parent_counter_get.exported) if self.imported is not None else None
        )


def get_counter_value_store(component_num: int,
                            add_child_values: bool = False,
                            simcounter: Optional[SimCounter] = None) -> PurgeCounterState:
    if compatibility.is_ramdisk_in_use():
        delegate = CounterValueStoreRamdisk()
    else:
        delegate = CounterValueStoreBroker(component_num)
    return PurgeCounterState(LoggingValueStore(delegate), add_child_values, simcounter)
