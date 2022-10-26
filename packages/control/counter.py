"""Zähler-Logik
"""
from dataclasses import dataclass, field
import logging

from control import data
from dataclass_utils.factories import emtpy_list_factory
from helpermodules.pub import Pub
from modules.common.fault_state import FaultStateLevel

log = logging.getLogger(__name__)


class Counter:
    """
    """

    def __init__(self, index):
        try:
            self.data = {"set": {},
                         "get": {
                "daily_exported": 0,
                "daily_imported": 0}}
            self.num = index
        except Exception:
            log.exception("Fehler in der Zähler-Klasse von "+str(self.num))

    def setup_counter(self):
        # Zählvariablen vor dem Start der Regelung zurücksetzen
        try:
            self._set_loadmanagement_state()
            if self.data["get"]["fault_state"] == FaultStateLevel.ERROR:
                self.data["get"]["power"] = 0
                return
            # Nur beim EVU-Zähler wird auch die maximale Leistung geprüft.
            if f'counter{self.num}' == data.data.counter_all_data.get_evu_counter():
                # max Leistung
                if self.data["get"]["power"] > 0:
                    self.data["set"]["consumption_left"] = self.data["config"]["max_total_power"] \
                        - self.data["get"]["power"]
                else:
                    self.data["set"]["consumption_left"] = self.data["config"]["max_total_power"]
                log.debug(str(self.data["set"]["consumption_left"]) +
                          "W EVU-Leistung, die noch bezogen werden kann.")
            # Strom
            try:
                self.data["set"]["currents_used"] = self.data["get"]["currents"]
            except KeyError:
                log.warning(f"Zähler {self.num}: Einzelwerte für Zähler-Phasenströme unbekannt")
                self.data["set"]["state_str"] = ("Das Lastmanagement regelt nur anhand der Gesamtleistung, da keine " +
                                                 "Phasenströme ermittelt werden konnten.")
                Pub().pub("openWB/set/counter/"+str(self.num) + "/set/state_str",
                          self.data["set"]["state_str"])
        except Exception:
            log.exception("Fehler in der Zähler-Klasse von "+str(self.num))

    def _set_loadmanagement_state(self) -> None:
        # Wenn der Zähler keine Werte liefert, darf nicht geladen werden.
        connected_cps = data.data.counter_all_data.get_chargepoints_of_counter(f'counter{self.num}')
        for cp in connected_cps:
            if self.data["get"]["fault_state"] == FaultStateLevel.ERROR:
                data.data.cp_data[cp].data.set.loadmanagement_available = False
            else:
                data.data.cp_data[cp].data.set.loadmanagement_available = True

    def put_stats(self):
        try:
            if f'counter{self.num}' == data.data.counter_all_data.get_evu_counter():
                Pub().pub("openWB/set/counter/"+str(self.num)+"/set/consumption_left",
                          self.data["set"]["consumption_left"])
                log.debug(str(self.data["set"]["consumption_left"])+"W verbleibende EVU-Bezugs-Leistung")
        except Exception:
            log.exception("Fehler in der Zähler-Klasse von "+str(self.num))

    def print_stats(self):
        try:
            log.debug(str(self.data["set"]["consumption_left"])+"W verbleibende EVU-Bezugs-Leistung")
        except Exception:
            log.exception("Fehler in der Zähler-Klasse von "+str(self.num))
