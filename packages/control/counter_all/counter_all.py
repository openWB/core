"""Zähler-Logik
"""
import copy
import logging
from typing import List, Tuple

from control import data
from control.counter import Counter
from control.counter_all.counter_all_data import CounterAllData
from control.counter_all.hierarchy import HierarchyMixin
from control.counter_all.loadmanagement_prio import LoadmanagementPrioMixin
from helpermodules.pub import Pub
from modules.common.component_type import ComponentType
from modules.common.fault_state import FaultStateLevel
from modules.common.simcount import SimCounter

log = logging.getLogger(__name__)


class CounterAll(HierarchyMixin, LoadmanagementPrioMixin):
    MISSING_EVU_COUNTER = "Bitte erst einen EVU-Zähler konfigurieren."

    def __init__(self):
        self.data = CounterAllData()
        self.sim_counter = SimCounter("", "", prefix="bezug")
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
            self._validate_home_consumption_counter()
            home_consumption, elements = self._calc_home_consumption()
            if home_consumption < 0:
                log.error(
                    f"Ungültiger Hausverbrauch: {home_consumption}W, Berücksichtigte Komponenten neben EVU {elements}")
                if self.data.config.home_consumption_source_id is None:
                    hc_counter_source = self.get_evu_counter_str()
                else:
                    hc_counter_source = f"counter{self.data.config.home_consumption_source_id}"
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

    EVU_IS_HC_COUNTER_ERROR = ("Der EVU-Zähler kann nicht als Quelle für den Hausverbrauch verwendet werden. Meist ist "
                               "der Zähler am EVU-Punkt installiert, dann muss im Lastmanagement unter Hausverbrauch"
                               " 'von openWB berechnen' ausgewählt werden. Wenn der Zähler im Hausverbrauchszweig "
                               "installiert ist, einen virtuellen Zähler anlegen und im Lastmanagement ganz links "
                               "anordnen.")

    def _validate_home_consumption_counter(self):
        if self.data.config.home_consumption_source_id is not None:
            if self.data.config.home_consumption_source_id == self.get_id_evu_counter():
                hc_counter_data = data.data.counter_data[self.get_evu_counter_str()].data
                hc_counter_data.get.fault_state = FaultStateLevel.ERROR.value
                hc_counter_data.get.fault_str = self.EVU_IS_HC_COUNTER_ERROR
                evu_counter = self.get_id_evu_counter()
                Pub().pub(f"openWB/set/counter/{evu_counter}/get/fault_state",
                          hc_counter_data.get.fault_state)
                Pub().pub(f"openWB/set/counter/{evu_counter}/get/fault_str",
                          hc_counter_data.get.fault_str)
                raise Exception(self.EVU_IS_HC_COUNTER_ERROR)

    def _calc_home_consumption(self) -> Tuple[float, List]:
        power = 0
        if self.data.config.home_consumption_source_id is None:
            id_source = self.get_id_evu_counter()
        else:
            id_source = self.data.config.home_consumption_source_id
        elements_to_sum_up = self.get_elements_for_downstream_calculation(id_source)
        for element in elements_to_sum_up:
            if element["type"] == ComponentType.CHARGEPOINT.value:
                component = data.data.cp_data[f"cp{element['id']}"]
            elif element["type"] == ComponentType.BAT.value:
                component = data.data.bat_data[f"bat{element['id']}"]
            elif element["type"] == ComponentType.COUNTER.value:
                component = data.data.counter_data[f"counter{element['id']}"]
            elif element["type"] == ComponentType.INVERTER.value:
                component = data.data.pv_data[f"pv{element['id']}"]

            if component.data.get.fault_state < 2:
                power += component.data.get.power
            else:
                log.warning(
                    f"Komponente {element['type']}{component.num} ist im Fehlerzustand und wird nicht berücksichtigt.")
        evu = data.data.counter_data[f"counter{id_source}"].data.get.power
        return evu - power - self.data.set.smarthome_power_excluded_from_home_consumption, elements_to_sum_up

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
