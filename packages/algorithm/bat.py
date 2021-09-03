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
Zieht die openWB nun Überschuss (15kW Überschuss + 5kW Batterieladung = 20kW) kommt es zu 5kW Bezug weil der Wechselrichter nur 15kW abgeben kann.

aktuell wird halt bei ev vorrang die Batterieladeleistung hinzugerechnet. weil die openWB von ausgeht das die dann das laden aufhört und diese leistung eignetlich überschuss ist.
Blöd halt wenn der WEchselrichter die nicht zur verfügung stellen kann.
Heißt aktuell denkt die openWB "0 Watt überschuss" weil 5kW bezogen werden, aber eben auch 5kW in die Batterie gehen (die ihre ladung aber nicht drosselt)

du musst halt zum "antesten" bezug generieren damit die Batterie entsprechend gegenregelt. erst wenn sie das nach x sekunden nicht tut kannst von ausgehen da gibt es eine Grenze

__Wie schnell regelt denn ein Speicher?
Je nach Speicher 1-4 Sekunden.
__Muss dann immer ein bisschen Überschuss über sein und wenn dieser im nächsten Zyklus noch da ist, kann der LP hochgeregelt werden. Wenn nicht muss der LP runtergeregelt werden?
Üblicherweise reicht es so zu regeln das rund 50 Watt Einspeisung da sind, dann "nimmt" der Speicher sich die von alleine
"""

from . import data
from ..helpermodules import log
from ..helpermodules import pub

class bat:
    def __init__(self):
        self.data={}
        if "get" not in self.data:
            self.data["get"]={}
        if "set" not in self.data:
            self.data["set"]={}
        if "config" not in self.data:
            self.data["config"]={}
        self.data["config"]["configured"] = False
        self.data["set"]["charging_power_left"] = 0
        self.data["set"]["switch_on_soc_reached"] = 0
        self.data["set"]["hybrid_system_detected"] = False

    def setup_bat(self):
        """ prüft, ob mind ein Speicher vorhanden ist und berechnet die Summentopics.
        """
        try:
            if len(data.data.bat_module_data) > 1:
                if "all" not in data.data.bat_module_data:
                    data.data.bat_module_data["all"] = {}
                self.data["config"]["configured"] = True
                # Summe für alle konfigurierten Speicher bilden
                soc_sum = 0
                soc_count = 0
                self.data["get"]["power"] = 0
                self.data["get"]["imported"] = 0
                self.data["get"]["exported"] = 0
                self.data["get"]["daily_yield_export"] = 0
                self.data["get"]["daily_yield_import"] = 0
                for bat in data.data.bat_module_data:
                    try:
                        if "bat" in bat:
                            self.data["get"]["power"] += data.data.bat_module_data[bat].data["get"]["power"]
                            self.data["get"]["imported"] += data.data.bat_module_data[bat].data["get"]["imported"]
                            self.data["get"]["exported"] += data.data.bat_module_data[bat].data["get"]["exported"]
                            self.data["get"]["daily_yield_export"] += data.data.bat_module_data[bat].data["get"]["daily_yield_export"]
                            self.data["get"]["daily_yield_import"] += data.data.bat_module_data[bat].data["get"]["daily_yield_import"]
                            soc_sum += data.data.bat_module_data[bat].data["get"]["soc"]
                            soc_count += 1
                    except Exception as e:
                        log.exception_logging(e)
                self.data["get"]["soc"] = int(soc_sum / soc_count)
                # Alle Summentopics im Dict publishen
                {pub.pub("openWB/set/bat/get/"+k, v)for (k,v) in self.data["get"].items()}
                # Speicher lädt
                if self.data["get"]["power"] > 0:
                   self._get_charging_power_left()
                # Speicher wird entladen -> Wert wird ebenfalls benötigt, um zu prüfen, ob Abschaltschwelle erreicht wird.
                else:
                    self.data["set"]["charging_power_left"] = self.data["get"]["power"]
                log.message_debug_log("debug", str(self.data["set"]["charging_power_left"])+"W verbliebende Speicher-Leistung")
            else:
                self.data["config"]["configured"] = False
                self.data["set"]["charging_power_left"] = 0
                self.data["get"]["power"] = 0
            pub.pub("openWB/set/bat/config/configured", self.data["config"]["configured"])
            pub.pub("openWB/set/bat/set/charging_power_left", self.data["set"]["charging_power_left"])
            pub.pub("openWB/set/bat/set/switch_on_soc_reached", self.data["set"]["switch_on_soc_reached"])
            pub.pub("openWB/set/bat/set/hybrid_system_detected", self.data["set"]["hybrid_system_detected"])
        except Exception as e:
            log.exception_logging(e)

    def _get_charging_power_left(self):
        """ ermittelt die Lade-Leistung des Speichers, die zum Laden der EV verwendet werden darf.
        """
        try:
            config = data.data.general_data["general"].data["chargemode_config"]["pv_charging"]
            if config["bat_prio"] == False:
                # Wenn der Speicher lädt und gleichzeitg Bezug da ist, sind entweder die Werte sehr ungünstig abgefragt worden 
                # (deshalb wird noch ein Zyklus gewartet) oder es liegt ein Hybrid-System vor.
                if data.data.counter_data["counter0"].data["get"]["power_all"] > 0:
                    if self.data["set"]["hybrid_system_detected"] == True:
                        self.data["set"]["charging_power_left"] = max(self.data["set"]["charging_power_left"] - data.data.counter_data["counter0"].data["get"]["power_all"], 0)
                    else:
                        self.data["set"]["hybrid_system_detected"] = True
                elif self.data["set"]["hybrid_system_detected"] == True:
                    self.data["set"]["hybrid_system_detected"] = False
                # Laderegelung wurde noch nicht freigegeben
                if self.data["set"]["switch_on_soc_reached"] == False:
                    if config["switch_on_soc"] != 0:
                        if config["switch_on_soc"] < self.data["get"]["soc"]:
                            self.data["set"]["switch_on_soc_reached"] = True
                            self.data["set"]["charging_power_left"] = self.data["get"]["power"]
                        else:
                            self.data["set"]["charging_power_left"] = 0
                    else:
                        # Kein Einschalt-Soc; Nutzung, wenn Soc über Ausschalt-Soc liegt.
                        if config["switch_off_soc"] != 0:
                            if config["switch_off_soc"] < self.data["get"]["soc"]:
                                self.data["set"]["switch_on_soc_reached"] = True
                                self.data["set"]["charging_power_left"] = self.data["get"]["power"]
                            else:
                                self.data["set"]["switch_on_soc_reached"] = False
                                self.data["set"]["charging_power_left"] = 0
                        # Weder Einschalt- noch Ausschalt-Soc sind konfiguriert.
                        else:
                            self.data["set"]["charging_power_left"] = self.data["get"]["power"]
                # Laderegelung wurde freigegeben.
                elif self.data["set"]["switch_on_soc_reached"] == True:
                    if config["switch_off_soc"] != 0:
                        # Greift der Ausschalt-Soc?
                        if config["switch_off_soc"] < self.data["get"]["soc"]:
                            self.data["set"]["charging_power_left"] = self.data["get"]["power"]
                        else:
                            self.data["set"]["switch_on_soc_reached"] = False
                            self.data["set"]["charging_power_left"] = 0
                    # Wenn kein Ausschalt-Soc konfiguriert wurde, wird der Speicher komplett entladen.
                    else:
                        if 0 < self.data["get"]["soc"]:
                            self.data["set"]["charging_power_left"] = self.data["get"]["power"]
                        else:
                            self.data["set"]["switch_on_soc_reached"] = False
                            self.data["set"]["charging_power_left"] = 0
                # Ladeleistungs-Reserve
                self.data["set"]["charging_power_left"] = self.data["set"]["charging_power_left"] - config["charging_power_reserve"]
            # Wenn der Speicher Vorrang hat, darf die erlaubte Entlade-Leistung zum Laden der EV genutzt werden, wenn der Soc über dem minimalen Entlade-Soc liegt.
            else:
                if config["rundown_soc"] != 100:
                    if self.data["get"]["soc"] > config["rundown_soc"]:
                        self.data["set"]["charging_power_left"] = config["rundown_power"]
                    else:
                        # 50 W Überschuss übrig lassen, die sich der Speicher dann nehmen kann. Wenn der Speicher schneller regelt, als die LP, würde sonst der Speicher reduziert werden.
                        self.data["set"]["charging_power_left"] = -50
                else:
                    self.data["set"]["charging_power_left"] = -50
        except Exception as e:
            log.exception_logging(e)

    def get_power(self):
        """ gibt die Leistung zurück, die gerade am Speicher anliegt (Summe, wenn es mehrere Speicher gibt).

        Return
        ------
        int: Leistung am Speicher
        """
        try:
            if self.data["config"]["configured"] == True:
                return self.data["get"]["power"]
            else:
                return 0
        except Exception as e:
            log.exception_logging(e)
            return 0

    def power_for_bat_charging(self):
        """ gibt die Leistung zurück, die zum Laden verwendet werden kann.

        Return
        ------
        int: Leistung, die zum Laden verwendet werden darf.
        """
        try:
            if self.data["config"]["configured"] == True:
                return self.data["set"]["charging_power_left"]
            else:
                return 0
        except Exception as e:
            log.exception_logging(e)
            return 0

    def allocate_bat_power(self, required_power):
        """ subtrahieren der zugeteilten Leistung von der verfügbaren Speicher-Leistung

        Parameter
        ---------
        required_power: float
            Leistung, mit der geladen werden soll

        Return
        ------
        True: Leistung konnte allokiert werden.
        False: Leistung konnte nicht allokiert werden.
        """
        try:
            if self.data["config"]["configured"] == True:
                self.data["set"]["charging_power_left"] -= required_power
                if self.data["set"]["charging_power_left"] < 0:
                    log.message_debug_log("error", "Es wurde versucht, mehr Speicher-Leistung zu allokieren, als geladen wird.")
                    too_much = self.data["set"]["charging_power_left"]
                    self.data["set"]["charging_power_left"] = 0
                    return too_much
            return 0
        except Exception as e:
            log.exception_logging(e)
            return required_power

    def put_stats(self):
        """ Publishen und Loggen der verbleibnden PV-Leistung und reservierten Leistung
        """
        try:
            pub.pub("openWB/set/bat/config/configured", self.data["config"]["configured"])
            if self.data["config"]["configured"] == True:
                pub.pub("openWB/set/bat/set/charging_power_left", self.data["set"]["charging_power_left"])
                log.message_debug_log("debug", str(self.data["set"]["charging_power_left"])+"W Speicher-Leistung , die fuer die folgenden Ladepunkte uebrig ist.")
        except Exception as e:
            log.exception_logging(e)

class batModule:

    def __init__(self, index):
        self.data={}
        self.bat_num = index
        self.data["get"] = {}
        self.data["get"]["daily_yield_import"] = 0
        self.data["get"]["daily_yield_export"] = 0
