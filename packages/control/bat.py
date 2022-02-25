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

aktuell wird halt bei ev vorrang die Batterieladeleistung hinzugerechnet. weil die openWB von ausgeht das die
dann das laden aufhört und diese leistung eigentlich Überschuss ist.
Blöd halt wenn der Wechselrichter die nicht zur Verfügung stellen kann.
Heißt aktuell denkt die openWB "0 Watt Überschuss" weil 5kW bezogen werden, aber eben auch 5kW in die Batterie
gehen (die ihre Ladung aber nicht drosselt)

du musst halt zum "antesten" bezug generieren damit die Batterie entsprechend gegenregelt. erst wenn sie das nach
 x Sekunden nicht tut kannst von ausgehen da gibt es eine Grenze

__Wie schnell regelt denn ein Speicher?
Je nach Speicher 1-4 Sekunden.
__Muss dann immer ein bisschen Überschuss über sein und wenn dieser im nächsten Zyklus noch da ist, kann der LP
hochgeregelt werden. Wenn nicht muss der LP runtergeregelt werden?
Üblicherweise reicht es so zu regeln das rund 50 Watt Einspeisung da sind, dann "nimmt" der Speicher sich die von
alleine
"""
import logging

from control import data
from helpermodules.pub import Pub

log = logging.getLogger(__name__)


class BatAll:
    def __init__(self):
        self.data = {
            "get": {"power":  0},
            "config": {"configured": False},
            "set": {"charging_power_left": 0,
                    "switch_on_soc_reached": 0,
                    "hybrid_system_detected": False}
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
                self.data["get"]["daily_yield_export"] = 0
                self.data["get"]["daily_yield_import"] = 0
                for bat in data.data.bat_data:
                    try:
                        if "bat" in bat:
                            battery = data.data.bat_data[bat]
                            self.data["get"]["power"] += battery.data["get"]["power"]
                            self.data["get"]["imported"] += battery.data["get"]["imported"]
                            self.data["get"]["exported"] += battery.data["get"]["exported"]
                            self.data["get"]["daily_yield_export"] += battery.data["get"]["daily_yield_export"]
                            self.data["get"]["daily_yield_import"] += battery.data["get"]["daily_yield_import"]
                            soc_sum += battery.data["get"]["soc"]
                            soc_count += 1
                    except Exception:
                        log.exception("Fehler im Bat-Modul "+bat)
                self.data["get"]["soc"] = int(soc_sum / soc_count)
                # Alle Summentopics im Dict publishen
                {Pub().pub("openWB/set/bat/get/"+k, v) for (k, v) in self.data["get"].items()}
            else:
                self.data["config"]["configured"] = False
                Pub().pub("openWB/set/bat/config/configured", self.data["config"]["configured"])
                {Pub().pub("openWB/bat/get/"+k, 0) for (k, _) in self.data["get"].items()}
        except Exception:
            log.exception("Fehler im Bat-Modul")

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
            Pub().pub("openWB/set/bat/set/hybrid_system_detected", self.data["set"]["hybrid_system_detected"])
        except Exception:
            log.exception("Fehler im Bat-Modul")

    def _get_charging_power_left(self):
        """ ermittelt die Lade-Leistung des Speichers, die zum Laden der EV verwendet werden darf.
        """
        try:
            evu_counter = data.data.counter_data["all"].get_evu_counter()
            config = data.data.general_data["general"].data["chargemode_config"]["pv_charging"]
            if not config["bat_prio"]:
                # Wenn der Speicher lädt und gleichzeitig Bezug da ist, sind entweder die Werte sehr ungünstig abgefragt
                # worden
                # (deshalb wird noch ein Zyklus gewartet) oder es liegt ein Hybrid-System vor.
                if data.data.counter_data[evu_counter].data["get"]["power"] > 0:
                    if self.data["set"]["hybrid_system_detected"]:
                        log.debug("".join(("verbleibende Speicher-Leistung für Hybrid-System: max(",
                                           self.data["set"]["charging_power_left"], " - ",
                                           data.data.counter_data[evu_counter].data["get"]["power"],
                                           ", 0)")))
                        self.data["set"]["charging_power_left"] = max(
                            self.data["set"]["charging_power_left"]
                            - data.data.counter_data[evu_counter].data["get"]["power"], 0)
                    else:
                        self.data["set"]["hybrid_system_detected"] = True
                        log.debug("Erstmalig Hybrid-System detektiert.")
                elif self.data["set"]["hybrid_system_detected"]:
                    self.data["set"]["hybrid_system_detected"] = False
                # Laderegelung wurde noch nicht freigegeben
                if not self.data["set"]["switch_on_soc_reached"]:
                    if config["switch_on_soc"] != 0:
                        if config["switch_on_soc"] < self.data["get"]["soc"]:
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
                        if config["switch_off_soc"] != 0:
                            if config["switch_off_soc"] < self.data["get"]["soc"]:
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
                    if config["switch_off_soc"] != 0:
                        # Greift der Ausschalt-Soc?
                        if config["switch_off_soc"] < self.data["get"]["soc"]:
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
                    config["charging_power_reserve"]
                log.debug("".join(("Ladeleistungs-Reserve subtrahieren: ",
                                   self.data["set"]["charging_power_left"], " = ",
                                   self.data["set"]["charging_power_left"], " - ",
                                   config["charging_power_reserve"])))
            # Wenn der Speicher Vorrang hat, darf die erlaubte Entlade-Leistung zum Laden der EV genutzt werden, wenn
            # der Soc über dem minimalen Entlade-Soc liegt.
            else:
                if config["rundown_soc"] != 100:
                    if self.data["get"]["soc"] > config["rundown_soc"]:
                        self.data["set"]["charging_power_left"] = config["rundown_power"]
                        log.debug("".join(
                            ("Erlaubte Entlade-Leistung nutzen (", str(config["rundown_power"]), "W)")))
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


class Bat:

    def __init__(self, index):
        self.data = {}
        self.bat_num = index
        self.data["get"] = {}
        self.data["get"]["daily_yield_import"] = 0
        self.data["get"]["daily_yield_export"] = 0
