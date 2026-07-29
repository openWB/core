"""Zähler-Logik
"""
import copy
import logging
from typing import Any, Dict, List, Tuple

from control import data
from control.counter import Counter
from control.counter_all.counter_all_data import CounterAllData
from control.counter_all.hierarchy import HierarchyMixin
from control.counter_all.loadmanagement_prio import LoadmanagementPrioMixin
from control.counter import Counter, CounterMode
from modules.common.component_type import ComponentType
from modules.common.fault_state import FaultStateLevel
from modules.common.simcount import SimCounter

log = logging.getLogger(__name__)


class CounterAll(HierarchyMixin, LoadmanagementPrioMixin):
    MISSING_EVU_COUNTER = "Bitte erst einen EVU-Zähler konfigurieren."

    def __init__(self):
        self.data = CounterAllData()
        # Hilfsvariablen für die rekursiven Funktionen
        self.connected_counters = []
        self.connected_chargepoints = []
        self.childless = []
        self.sim_counter = SimCounter("", "", ComponentType.COUNTER.value)
        self.sim_counter.topic = "openWB/set/counter/set/"

    def get_evu_counter(self) -> Counter:
        return data.data.counter_data[f"counter{self.get_id_evu_counter()}"]

    def get_evu_counter_str(self) -> str:
        return f"counter{self.get_id_evu_counter()}"

    def get_id_evu_counter(self) -> int:
        try:
            if ComponentType.COUNTER.value == self.data.get.hierarchy[0]["type"]:
                return self.data.get.hierarchy[0]['id']
            else:
                raise TypeError
        except Exception:
            log.error(
                "Ohne Konfiguration eines EVU-Zählers an der Spitze der Hierarchie ist keine Regelung und keine Ladung "
                "möglich.")
            raise

    def set_home_consumption(self) -> None:
        try:
            home_consumption, elements = self._calc_home_consumption()
            if home_consumption < 0:
                log.error(
                    f"Ungültiger Hausverbrauch: {home_consumption}W, Berücksichtigte Komponenten neben EVU {elements}")
                hc_counter_source = self.get_evu_counter_str()
                hc_counter_data = data.data.counter_data[hc_counter_source].data
                if hc_counter_data.get.fault_state == FaultStateLevel.NO_ERROR:
                    hc_counter_data.get.fault_state = FaultStateLevel.WARNING.value
                    hc_counter_data.get.fault_str = ("Hinweis: Es gibt mehr Stromerzeuger im Haus als in der openWB "
                                                     "eingetragen sind. Der Hausverbrauch kann nicht korrekt berechnet "
                                                     "werden. Dies hat auf die PV-Überschussladung keine negativen "
                                                     "Auswirkungen.")
                if self.data.set.invalid_home_consumption < 3:
                    self.data.set.invalid_home_consumption += 1
                    return
                else:
                    home_consumption = 0
            else:
                self.data.set.invalid_home_consumption = 0
            self.data.set.home_consumption = home_consumption
            imported, _ = self.sim_counter.sim_count(self.data.set.home_consumption)
            self.data.set.imported_home_consumption = imported
        except Exception:
            log.exception("Fehler in der allgemeinen Zähler-Klasse")

    def _get_component(self, element: Dict) -> Any:
        if element["type"] == ComponentType.COUNTER.value:
            return data.data.counter_data[f"counter{element['id']}"]
        elif element["type"] == ComponentType.CHARGEPOINT.value:
            return data.data.cp_data[f"cp{element['id']}"]
        elif element["type"] == ComponentType.BAT.value:
            return data.data.bat_data[f"bat{element['id']}"]
        elif element["type"] == ComponentType.INVERTER.value:
            return data.data.pv_data[f"pv{element['id']}"]
        else:
            raise ValueError(f"Unbekannter Komponententyp: {element['type']}")

    def _get_is_home_consumption(self, counter: Counter, parent_home_consumption: str) -> str:
        # Wenn auto ausgeählt ist, wird die einstellung vom Parent übernommen
        # Wenn nicht, wird die Einstellung vom Zähler selbst genommen
        if counter.data.config.is_home_consumption_counter == CounterMode.AUTO_HOME_CONSUMPTION.value:
            return parent_home_consumption

        return counter.data.config.is_home_consumption_counter

    def _get_local_power_from_counter(self, element: Dict) -> float:
        # Wird nur von Countern aufgerufen
        # Gib den lokalen Verbrauch des Zählers zurück
        # Bewertet noch nicht, ob Hausverbrauch oder nicht
        local_power = data.data.counter_data[f"counter{element['id']}"].data.get.power

        for child in element["children"]:
            comp = self._get_component(child)

            if comp.data.get.fault_state < 2:
                local_power -= comp.data.get.power
            else:
                log.warning(
                    f"Komponente {element['type']}{comp.num} ist im Fehlerzustand und wird nicht berücksichtigt.")

        return local_power

    def _calc_home_consumption_from_counter(
            self, element: Dict, parent_home_consumption: str) -> float:
        # Wird nur von Countern aufgerufen
        # Bewertet, ob Hausverbrauch oder nicht
        # Gibt den Hausverbrauch des Zählers zurück

        home_consumption = 0.0
        local_power = self._get_local_power_from_counter(element)

        counter = self._get_component(element)
        child_home_consumption = self._get_is_home_consumption(counter, parent_home_consumption)

        if child_home_consumption == CounterMode.HOME_CONSUMPTION.value:
            home_consumption += local_power

        for child in element["children"]:
            comp = self._get_component(child)

            if comp.data.get.fault_state < 2:
                if child["type"] == ComponentType.COUNTER.value:
                    home_consumption += self._calc_home_consumption_from_counter(child, child_home_consumption)
            else:
                log.warning(
                    f"Komponente {element['type']}{comp.num} ist im Fehlerzustand und wird nicht berücksichtigt.")

        return home_consumption

    def _calc_home_consumption(self) -> Tuple[float, Dict]:
        evu_id = self.get_id_evu_counter()

        # get_elements_for_downstream_calculation berücksichtigt Hybrid-Batterien
        # wo die Bat im Wechselrichter ist (als child) und nicht direkt unter einem Zähler hängt
        #
        # get_elements_for_downstream_calculation liefert nur die Elemente unterhalb des EVU.
        # Für die Rekursion bauen wir daher ein virtuelles Root-Element für den EVU-Zähler,
        # ohne die echte Hierarchie zu verändern.

        elements = self.get_elements_for_downstream_calculation(evu_id)
        evu_element = {"id": evu_id, "type": ComponentType.COUNTER.value, "children": elements}

        home_consumption = 0.0

        # Rekursion startet immer beim EVU-Zähler.
        home_consumption = self._calc_home_consumption_from_counter(evu_element, CounterMode.NOT_HOME_CONSUMPTION.value)

        home_consumption -= self.data.set.smarthome_power_excluded_from_home_consumption

        return home_consumption, evu_element

    def _add_hybrid_bat(self, id: int) -> List:
        elements = []
        inverter_children = self.get_entry_of_element(id)["children"]
        for child in inverter_children:
            if child["type"] == ComponentType.BAT.value:
                elements.append(child)
        return elements

    def get_elements_for_downstream_calculation(self, id: int):
        """returns a list of elements that are relevant for the calculation of the counter values based on the
        downstream components, eg home consumption or virtual counter."""
        elements = copy.deepcopy(self.get_entry_of_element(id)["children"])
        elements_to_sum_up = elements
        for element in elements:
            if element["type"] == ComponentType.INVERTER.value:
                elements_to_sum_up.extend(self._add_hybrid_bat(element['id']))
        return elements_to_sum_up

    def _is_home_consumption_counter_by_id(self, counter_id: int) -> str:
        counter_entry = self.get_entry_of_element(counter_id)
        if not counter_entry:
            raise IndexError(f"Element {counter_id} konnte nicht in der Hierarchie gefunden werden.")
        if counter_entry["type"] != ComponentType.COUNTER.value:
            raise ValueError(f"Element {counter_id} ist kein Zähler.")

        counter_obj = data.data.counter_data[f"counter{counter_id}"]

        # Explizite Einstellung hat Vorrang, nur Auto wird vom Parent geerbt.
        if not counter_obj.data.config.is_home_consumption_counter == CounterMode.AUTO_HOME_CONSUMPTION.value:
            return counter_obj.data.config.is_home_consumption_counter

        parent = self.get_entry_of_parent(counter_id)
        if not parent or parent["type"] != ComponentType.COUNTER.value:
            # Auto am Wurzel-Zähler entspricht dem bisherigen Startwert CounterMode.NOT_HOME_CONSUMPTION.
            return CounterMode.NOT_HOME_CONSUMPTION.value

        return self._is_home_consumption_counter_by_id(parent["id"])

    def is_home_consumption_counter(self, counter_id: int) -> bool:
        """Ermittelt den effektiven Home-Consumption-Status eines Zählers.
        Berücksichtigt den Auto-Parameter entlang aller übergeordneten Zähler.
        """
        return self._is_home_consumption_counter_by_id(counter_id) == CounterMode.HOME_CONSUMPTION.value


def get_max_id_in_hierarchy(current_entry: List, max_id: int) -> int:
    for item in current_entry:
        if item["id"] > max_id:
            max_id = item["id"]
        if len(item["children"]) != 0:
            max_id = get_max_id_in_hierarchy(item["children"], max_id)
    else:
        return max_id


def get_counter_default_config():
    return {"max_currents": [16, 16, 16],
            "max_total_power": 11000}
