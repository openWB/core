"""Hausspeicher-Logik
Der Hausspeicher ist immer bestrebt, den EVU-Überschuss auf 0 zu regeln.
Wenn EVU_Überschuss vorhanden ist, lädt der Speicher. Wenn EVU-Bezug vorhanden wäre,
entlädt der Speicher, sodass kein Netzbezug stattfindet. Wenn das EV Vorrang hat, wird
eine Ladung gestartet und der Speicher hört automatisch auf zu laden, da sonst durch
das Laden des EV Bezug statt finden würde.

Sonderfall Hybrid-Systeme:
Wenn wir ein Hybrid Wechselrichter Speicher system haben das besteht aus:
20 kW PV
15kW Wechselrichter
Batterie DC
Kann es derzeit passieren das die PV 20kW erzeugt, die Batterie mit 5kW geladen wird und 15kW ins Netz gehen.
Zieht die openWB nun Überschuss (15kW Überschuss + 5kW Batterieladung = 20kW) kommt es zu 5kW Bezug weil der
Wechselrichter nur 15kW abgeben kann.

__Wie schnell regelt ein Speicher?
Je nach Speicher 1-4 Sekunden.
"""
import logging

from control import data
from helpermodules.pub import Pub
from modules.common.fault_state import FaultStateLevel

log = logging.getLogger(__name__)


class Bat:

    def __init__(self, index):
        self.data = {}
        self.num = index
        self.data["get"] = {}
        self.data["get"]["daily_imported"] = 0
        self.data["get"]["daily_exported"] = 0


class BatAll:
    def __init__(self):
        self.data = {
            "get": {"power":  0},
            "config": {"configured": False},
            "set": {"charging_power_left": 0,
                    "switch_on_soc_reached": 0}
        }

    def calc_power_for_all_components(self):
        try:
            if len(data.data.bat_data) > 1:
                self.data["config"]["configured"] = True
                Pub().pub("openWB/set/bat/config/configured", self.data["config"]["configured"])
                # Summe für alle konfigurierten Speicher bilden
                soc_sum = 0
                soc_count = 0
                self.data["get"]["power"] = 0
                self.data["get"]["imported"] = 0
                self.data["get"]["exported"] = 0
                self.data["get"]["daily_exported"] = 0
                self.data["get"]["daily_imported"] = 0
                for battery in data.data.bat_data.values():
                    if isinstance(battery, Bat):
                        try:
                            self.data["get"]["power"] += self.__max_bat_power_hybrid_system(battery)
                            self.data["get"]["imported"] += battery.data["get"]["imported"]
                            self.data["get"]["exported"] += battery.data["get"]["exported"]
                            self.data["get"]["daily_exported"] += battery.data["get"]["daily_exported"]
                            self.data["get"]["daily_imported"] += battery.data["get"]["daily_imported"]
                            soc_sum += battery.data["get"]["soc"]
                            soc_count += 1
                        except Exception:
                            log.exception(f"Fehler im Bat-Modul {battery.num}")
                self.data["get"]["soc"] = int(soc_sum / soc_count)
                # Alle Summentopics im Dict publishen
                {Pub().pub("openWB/set/bat/get/"+k, v) for (k, v) in self.data["get"].items()}
            else:
                self.data["config"]["configured"] = False
                Pub().pub("openWB/set/bat/config/configured", self.data["config"]["configured"])
                {Pub().pub("openWB/bat/get/"+k, 0) for (k, _) in self.data["get"].items()}
        except Exception:
            log.exception("Fehler im Bat-Modul")

    def __max_bat_power_hybrid_system(self, battery: Bat) -> float:
        if battery.data["get"]["power"] > 0:
            parent = data.data.counter_all_data.get_entry_of_parent(battery.num)
            if parent.get("type") == "inverter":
                parent_data = data.data.pv_data[f"pv{parent['id']}"].data
                # Bei einem Hybrid-System darf die Summe aus Batterie-Ladeleistung, die für den Algorithmus verwendet
                # werden soll und PV-Leistung nicht größer als die max Ausgangsleistung des WR sein.
                if parent_data["config"]["max_ac_out"] > 0:
                    max_bat_power = parent_data["config"]["max_ac_out"]*-1 - parent_data["get"]["power"]
                    if battery.data["get"]["power"] > max_bat_power:
                        if battery.data["get"]["fault_state"] == FaultStateLevel.NO_ERROR:
                            battery.data["get"]["fault_state"] = FaultStateLevel.WARNING.value
                            battery.data["get"]["fault_str"] = ("Die maximale Entladeleistung des Wechselrichters" +
                                                                " ist erreicht.")
                            Pub().pub(f"openWB/set/bat/{battery.num}/get/fault_state",
                                      battery.data["get"]["fault_state"])
                            Pub().pub(f"openWB/set/bat/{battery.num}/get/fault_str",
                                      battery.data["get"]["fault_str"])
                        log.warning(
                            f"Bat {battery.num}: Die maximale Entladeleistung des Wechselrichters ist erreicht.")
                    return max(battery.data["get"]["power"], max_bat_power)
        return battery.data["get"]["power"]

    def setup_bat(self):
        """ prüft, ob mind ein Speicher vorhanden ist und berechnet die Summentopics.
        """
        try:
            if self.data["config"]["configured"] is True:
                # Speicher lädt
                if self.data["get"]["power"] > 0:
                    self._get_charging_power_left()
                # Speicher wird entladen -> Wert wird ebenfalls benötigt, um zu prüfen, ob Abschaltschwelle erreicht
                # wird.
                else:
                    self.data["set"]["charging_power_left"] = self.data["get"]["power"]
                log.info(
                    str(self.data["set"]["charging_power_left"])+"W verbliebende Speicher-Leistung")
            else:
                self.data["set"]["charging_power_left"] = 0
                self.data["get"]["power"] = 0
            Pub().pub("openWB/set/bat/set/charging_power_left", self.data["set"]["charging_power_left"])
            Pub().pub("openWB/set/bat/set/switch_on_soc_reached", self.data["set"]["switch_on_soc_reached"])
        except Exception:
            log.exception("Fehler im Bat-Modul")

    def _get_charging_power_left(self):
        """ ermittelt die Lade-Leistung des Speichers, die zum Laden der EV verwendet werden darf.
        """
        try:
            config = data.data.general_data.data.chargemode_config.pv_charging
            if not config.bat_prio:
                # Laderegelung wurde noch nicht freigegeben
                if not self.data["set"]["switch_on_soc_reached"]:
                    if config.switch_on_soc != 0:
                        if config.switch_on_soc < self.data["get"]["soc"]:
                            self.data["set"]["switch_on_soc_reached"] = True
                            self.data["set"]["charging_power_left"] = self.data["get"]["power"]
                        else:
                            self.data["set"]["charging_power_left"] = 0
                        log.debug(
                            "".join(
                                ("Laderegelung wurde ", "freigegeben."
                                 if self.data["set"]["switch_on_soc_reached"] else
                                 "nicht freigegeben, da Einschalt-SoC nicht erreicht.",
                                 " Verbleibene Speicher-Leistung: ", self.data["set"]["charging_power_left"],
                                 "W")))
                    else:
                        # Kein Einschalt-Soc; Nutzung, wenn Soc über Ausschalt-Soc liegt.
                        if config.switch_off_soc != 0:
                            if config.switch_off_soc < self.data["get"]["soc"]:
                                self.data["set"]["switch_on_soc_reached"] = True
                                self.data["set"]["charging_power_left"] = self.data["get"]["power"]
                            else:
                                self.data["set"]["switch_on_soc_reached"] = False
                                self.data["set"]["charging_power_left"] = 0
                            log.debug(
                                "".join(
                                    ("Laderegelung wurde ", "freigegeben."
                                     if self.data["set"]["switch_on_soc_reached"] else
                                     "nicht freigegeben, da Ausschalt-SoC erreicht.",
                                     " Verbleibene Speicher-Leistung: ", self.data["set"]["charging_power_left"],
                                     "W")))
                        # Weder Einschalt- noch Ausschalt-Soc sind konfiguriert.
                        else:
                            self.data["set"]["charging_power_left"] = self.data["get"]["power"]
                # Laderegelung wurde freigegeben.
                elif self.data["set"]["switch_on_soc_reached"]:
                    if config.switch_off_soc != 0:
                        # Greift der Ausschalt-Soc?
                        if config.switch_off_soc < self.data["get"]["soc"]:
                            self.data["set"]["charging_power_left"] = self.data["get"]["power"]
                        else:
                            self.data["set"]["switch_on_soc_reached"] = False
                            self.data["set"]["charging_power_left"] = 0
                        log.debug(
                            "".join(
                                ("Laderegelung wurde ", "freigegeben."
                                 if self.data["set"]["switch_on_soc_reached"] else
                                 "nicht freigegeben, da Ausschalt-SoC erreicht.",
                                 " Verbleibene Speicher-Leistung: ", self.data["set"]["charging_power_left"],
                                 "W")))
                    # Wenn kein Ausschalt-Soc konfiguriert wurde, wird der Speicher komplett entladen.
                    else:
                        if 0 < self.data["get"]["soc"]:
                            self.data["set"]["charging_power_left"] = self.data["get"]["power"]
                        else:
                            self.data["set"]["switch_on_soc_reached"] = False
                            self.data["set"]["charging_power_left"] = 0
                        log.debug(
                            "".join(
                                ("Laderegelung wurde ", "freigegeben, da der Speicher komplett entladen werden darf."
                                 if self.data["set"]["switch_on_soc_reached"] else "nicht freigegeben.",
                                 " Verbleibene Speicher-Leistung: ", self.data["set"]["charging_power_left"],
                                 "W")))
                # Ladeleistungs-Reserve
                self.data["set"]["charging_power_left"] = self.data["set"]["charging_power_left"] - \
                    config.charging_power_reserve
                log.debug(f'Ladeleistungs-Reserve subtrahieren: {self.data["set"]["charging_power_left"]} = '
                          f'{self.data["set"]["charging_power_left"]} - {config.charging_power_reserve}')
            # Wenn der Speicher Vorrang hat, darf die erlaubte Entlade-Leistung zum Laden der EV genutzt werden, wenn
            # der Soc über dem minimalen Entlade-Soc liegt.
            else:
                if config.rundown_soc != 100:
                    if self.data["get"]["soc"] > config.rundown_soc:
                        self.data["set"]["charging_power_left"] = config.rundown_power
                        log.debug(f"Erlaubte Entlade-Leistung nutzen ({config.rundown_power}W)")
                    else:
                        # 50 W Überschuss übrig lassen, die sich der Speicher dann nehmen kann. Wenn der Speicher
                        # schneller regelt, als die LP, würde sonst der Speicher reduziert werden.
                        self.data["set"]["charging_power_left"] = -50
                else:
                    self.data["set"]["charging_power_left"] = -50
        except Exception:
            log.exception("Fehler im Bat-Modul")

    def get_power(self):
        """ gibt die Leistung zurück, die gerade am Speicher anliegt (Summe, wenn es mehrere Speicher gibt).

        Return
        ------
        int: Leistung am Speicher
        """
        try:
            if self.data["config"]["configured"]:
                return self.data["get"]["power"]
            else:
                return 0
        except Exception:
            log.exception("Fehler im Bat-Modul")
            return 0

    def power_for_bat_charging(self):
        """ gibt die Leistung zurück, die zum Laden verwendet werden kann.

        Return
        ------
        int: Leistung, die zum Laden verwendet werden darf.
        """
        try:
            if self.data["config"]["configured"]:
                return self.data["set"]["charging_power_left"]
            else:
                return 0
        except Exception:
            log.exception("Fehler im Bat-Modul")
            return 0

    def allocate_bat_power(self, required_power):
        """ subtrahieren der zugeteilten Leistung von der verfügbaren Speicher-Leistung

        Parameter
        ---------
        required_power: float
            Leistung, mit der geladen werden soll

        Return
        ------
        True: Leistung konnte zugeteilt werden.
        False: Leistung konnte nicht zugeteilt werden.
        """
        try:
            if self.data["config"]["configured"]:
                self.data["set"]["charging_power_left"] -= required_power
                if self.data["set"]["charging_power_left"] < 0:
                    log.error(
                        "Es wurde versucht, mehr Speicher-Leistung zuzuteilen, als geladen wird.")
                    too_much = self.data["set"]["charging_power_left"]
                    self.data["set"]["charging_power_left"] = 0
                    return too_much
            return 0
        except Exception:
            log.exception("Fehler im Bat-Modul")
            return required_power

    def put_stats(self):
        """ Publishen und Loggen der verbleibenden PV-Leistung und reservierten Leistung
        """
        try:
            Pub().pub("openWB/set/bat/config/configured",
                      self.data["config"]["configured"])
            if self.data["config"]["configured"]:
                Pub().pub("openWB/set/bat/set/charging_power_left",
                          self.data["set"]["charging_power_left"])
                log.info(str(self.data["set"]["charging_power_left"]) +
                         "W Speicher-Leistung , die für die folgenden Ladepunkte übrig ist.")
        except Exception:
            log.exception("Fehler im Bat-Modul")
