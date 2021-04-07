""" EV-Logik
ermittelt, den Ladestrom, den das EV gerne zur Verfügung hätte.
"""

import data
import general
import log
import optional
import pub
import timecheck


def get_ev_to_rfid(rfid):
    """ sucht zur übergebenen RFID-ID das EV.

    Parameter
    ---------
    rfid: int
        Tag-ID

    Return
    ------
    vehicle: int
        Nummer des EV, das zum Tag gehört
    """
    for vehicle in data.ev_data:
        if "ev" in vehicle:
            try:
                if data.ev_data[vehicle].data["match_ev"]["selected"] == "rfid":
                    if data.ev_data[vehicle].data["match_ev"]["tag_id"] == rfid:
                        return data.ev_data[vehicle].ev_num
            except Exception as e:
                log.exception_logging(e)
    else:
        return None


class ev():
    """Logik des EV
    """

    def __init__(self, index):
        self.data = {}
        self.ev_template = None
        self.charge_template = None
        self.ev_num = index
        if "set" not in self.data:
            self.data["set"] = {}
        if "control_parameter" not in self.data:
            self.data["control_parameter"] = {}
        pub.pub("openWB/set/vehicle/"+str(self.ev_num) +
                "/control_parameter/required_current", 0)
        pub.pub("openWB/set/vehicle/"+str(self.ev_num) +
                "/control_parameter/timestamp_switch_on_off", "0")
        pub.pub("openWB/set/vehicle/"+str(self.ev_num) +
                "/control_parameter/timestamp_auto_phase_switch", "0")
        pub.pub("openWB/set/vehicle/"+str(self.ev_num) +
                "/control_parameter/chargemode", "stop")

    def get_required_current(self):
        """ ermittelt, ob und mit welchem Strom das EV geladen werden soll (unabhängig vom Lastmanagement)

        Return
        ------
        required_current: int
            Strom, der nach Ladekonfiguration benötigt wird
        """
        chargemode = None
        required_current = None
        try:
            if self.charge_template.data["chargemode"]["selected"] == "scheduled_charging":
                required_current, chargemode = self.charge_template.scheduled_charging(
                    self.data["get"]["soc"], self.ev_template.data["max_current"], self.ev_template.data["battery_capacity"], self.ev_template.data["max_phases"])
            elif self.charge_template.data["time_charging"]["active"] == True:
                required_current, chargemode = self.charge_template.time_charging()
            if (required_current == 0) or (required_current == None):
                if self.charge_template.data["chargemode"]["selected"] == "instant_charging":
                    required_current, chargemode = self.charge_template.instant_charging(
                        self.data["get"]["soc"], self.data["get"]["charged_since_plugged_kwh"])
                elif self.charge_template.data["chargemode"]["selected"] == "pv_charging":
                    required_current, chargemode = self.charge_template.pv_charging(
                        self.data["get"]["soc"])
                elif self.charge_template.data["chargemode"]["selected"] == "standby":
                    required_current, chargemode = self.charge_template.standby(
                        self.charge_template.data["chargemode"]["selected"])
            if chargemode == "stop" or (self.charge_template.data["chargemode"]["selected"] == "stop"):
                log.message_debug_log(
                    "debug", "EV"+str(self.ev_num)+": Lademdous stop")
                return False
            else:
                required_current = self._check_min_max_current(
                    required_current)
                self.data["control_parameter"]["required_current"] = required_current
                pub.pub("openWB/set/vehicle/"+self.ev_num +
                        "/control_parameter/required_current", required_current)
                self.data["control_parameter"]["chargemode"] = chargemode
                pub.pub("openWB/set/vehicle/"+self.ev_num +
                        "/control_parameter/chargemode", chargemode)
                log.message_debug_log("debug", "EV"+str(self.ev_num)+": Theroretisch benötigter Strom "+str(required_current)+"A, Lademodus "+str(
                    self.charge_template.data["chargemode"]["selected"])+", Submodus: "+str(chargemode)+", Prioritaet: "+str(self.charge_template.data["prio"]))
                return True
        except Exception as e:
            log.exception_logging(e)

    def get_soc(self):
        """ermittelt den SoC, wenn die Zugangsdaten konfiguriert sind.
        """
        pass

    def _check_min_max_current(self, required_current):
        """ prüft, ob der gesetzte Ladestrom über dem Mindest-Ladestrom und unter dem Maximal-Ladestrom des EVs liegt. Falls nicht, wird der 
        Ladestrom auf den Mindest-Ladestrom bzw. den Maximal-Ladestrom des EV gesetzt.

        Parameter
        ---------
        required_current: float
            Strom, der vom Lademodus benötgt wird

        Return
        ------
        float: Strom, mit dem das EV laden darf
        """
        try:
            if required_current != 0:
                if required_current < self.ev_template.data["min_current"]:
                    return self.ev_template.data["min_current"]
                if required_current > self.ev_template.data["max_current"]:
                    return self.ev_template.data["max_current"]
            return required_current
        except Exception as e:
            log.exception_logging(e)

    def check_min_max_current_for_pv_charging(self, required_current):
        """ prüft, ob der gesetzte Ladestrom über dem Mindest-Ladestrom des Lademdous und unter dem Maximal-Ladestrom des EVs liegt. Falls nicht, wird der 
        Ladestrom auf den Mindest-Ladestrom bzw. den Maximal-Ladestrom gesetzt.

        Parameter
        ---------
        required_current: float
            Strom, der vom Lademodus benötgt wird

        Return
        ------
        float: Strom, mit dem das EV laden darf
        """
        try:
            if required_current != 0:
                if required_current < self.data["control_parameter"]["required_current"]:
                    return self.data["control_parameter"]["required_current"]
                if required_current > self.ev_template.data["max_current"]:
                    return self.ev_template.data["max_current"]
            return required_current
        except Exception as e:
            log.exception_logging(e)

    def auto_phase_switch(self, phases_in_use, current_get):
        """ prüft, ob ein Timer für die Phasenumschaltung gestartet oder gestoppt werden muss oder ein Timer für die Phasenumschaltung abgelaufen ist.

        Parameter
        ---------
        phases_in_use: int
            Anzahl der aktuell genutzten Phasen
        current_get: list
            Stromstärke, mit der aktuell geladen wird

        Return
        ------
        phases_to_use: int
            Phasenanzahl , mit der geladen werden soll.
        """
        try:
            pv_config = data.general_data["general"].data["chargemode_config"]["pv_charging"]
            phases_to_use = phases_in_use
            if phases_in_use == 1:
                # Wenn im einphasigen Laden mit Maximalstromstärke geladen wird und der Timer abläuft, wird auf 3 Phasen umgeschaltet.
                if self.data["control_parameter"]["timestamp_auto_phase_switch"] != "0" and current_get[0] == self.ev_template.data["max_current"]:
                    if timecheck.check_timestamp(self.data["control_parameter"]["timestamp_auto_phase_switch"], pv_config["phase_switch_delay"]*60) == False:
                        phases_to_use = 3
                        self.data["control_parameter"]["timestamp_auto_phase_switch"] = "0"
                        pub.pub("openWB/set/vehicle/"+str(self.ev_num) + "/control_parameter/timestamp_auto_phase_switch", "0")
                        log.message_debug_log("info", "Umschaltung von 1 auf 3 Phasen.")
                # Wenn im einphasigen Laden die Maximalstromstärke erreicht wird und der Timer noch nicht läuft, Timer für das Umschalten auf 3 Phasen starten.
                elif self.data["control_parameter"]["timestamp_auto_phase_switch"] == "0" and current_get[0] == self.ev_template.data["max_current"]:
                    self.data["control_parameter"]["timestamp_auto_phase_switch"] = timecheck.create_timestamp()
                    pub.pub("openWB/set/vehicle/"+str(self.ev_num) +
                        "/control_parameter/timestamp_auto_phase_switch", self.data["control_parameter"]["timestamp_auto_phase_switch"])
                    log.message_debug_log("info", "Umschaltverzoegerung von 1 auf 3 Phasen für "+str(
                        pv_config["phase_switch_delay"]) + "Min aktiv.")
                # Wenn der Timer läuft und nicht mit Maximalstromstärke geladen wird, Timer stoppen.
                elif self.data["control_parameter"]["timestamp_auto_phase_switch"] != "0" and current_get[0] < self.ev_template.data["max_current"]:
                    self.data["control_parameter"]["timestamp_auto_phase_switch"] = "0"
                    pub.pub("openWB/set/vehicle/"+str(self.ev_num) +
                            "/control_parameter/timestamp_auto_phase_switch", "0")
                    log.message_debug_log("info", "Umschaltverzoegerung von 1 auf 3 Phasen abgebrochen.")
            elif phases_in_use == 3:
                if self.data["control_parameter"]["timestamp_auto_phase_switch"] != "0" and all(current == self.ev_template.data["min_current"] for current in current_get):
                    if timecheck.check_timestamp(self.data["control_parameter"]["timestamp_auto_phase_switch"], (16-pv_config["phase_switch_delay"])*60) == False:
                        phases_to_use = 1
                        self.data["control_parameter"]["timestamp_auto_phase_switch"] = "0"
                        pub.pub("openWB/set/vehicle/"+str(self.ev_num) + "/control_parameter/timestamp_auto_phase_switch", "0")
                        log.message_debug_log("info", "Umschaltung von 3 auf 1 Phase.")
                # Wenn im dreiphasigen Laden die Minimalstromstärke erreicht wird und der Timer noch nicht läuft, Timer für das Umschalten auf eine Phase starten.
                elif self.data["control_parameter"]["timestamp_auto_phase_switch"] == "0" and all(current == self.data["control_parameter"]["required_current"] for current in current_get):
                    self.data["control_parameter"]["timestamp_auto_phase_switch"] = timecheck.create_timestamp()
                    pub.pub("openWB/set/vehicle/"+str(self.ev_num) + "/control_parameter/timestamp_auto_phase_switch", self.data["control_parameter"]["timestamp_auto_phase_switch"])
                    log.message_debug_log("info", "Umschaltverzoegerung von 3 auf 1 Phase für "+str(
                        pv_config["phase_switch_delay"]) + "Min aktiv.")
                # Wenn der Timer läuft und mit mehr als Minimalstromstärke geladen wird, Timer stoppen.
                elif self.data["control_parameter"]["timestamp_auto_phase_switch"] != "0" and any(current > self.data["control_parameter"]["required_current"] for current in current_get):
                    self.data["control_parameter"]["timestamp_auto_phase_switch"] = "0"
                    pub.pub("openWB/set/vehicle/"+str(self.ev_num) + "/control_parameter/timestamp_auto_phase_switch", "0")
                    log.message_debug_log("info", "Umschaltverzoegerung von 3 auf 1 Phase abgebrochen.")
            return phases_to_use
        except Exception as e:
            log.exception_logging(e) 

    def load_default_profile(self):
        """ prüft, ob nach dem Abstecken das Standardprofil geladen werden soll und lädt dieses ggf..
        """
        pass

    def lock_cp(self):
        """prüft, ob nach dem Abstecken der LP gesperrt werden soll und sperrt diesen ggf..
        """
        pass


class evTemplate():
    """ Klasse mit den EV-Daten
    """

    def __init__(self):
        self.data = {}


class chargeTemplate():
    """ Klasse der Lademodus-Vorlage
    """

    def __init__(self):
        self.data = {}

    def time_charging(self):
        """ prüft, ob ein Zeitfenster aktiv ist und setzt entsprechend den Ladestrom
        """
        try:
            plan = timecheck.check_plans_timeframe(self.data["time_charging"])
            if plan != None:
                return self.data["time_charging"][plan]["current"], "time_charging"
            else:
                return 0, "time_charging"
        except Exception as e:
            log.exception_logging(e)

    def instant_charging(self, soc, amount):
        """ prüft, ob die Lademengenbegrenzung erreicht wurde und setzt entsprechend den Ladestrom.

        Parameter
        ---------
        soc: int
            SoC des EV

        amount: int
            geladende Energiemenge seit das EV angesteckt wurde
        """
        try:
            instant_charging = self.data["chargemode"]["instant_charging"]
            if data.optional_data["optional"].data["et"]["active"] == True:
                if data.optional_data["optional"].et_price_lower_than_limit() == False:
                    return 0, "instant_charging"
            if instant_charging["limit"]["selected"] == "none":
                return instant_charging["current"], "instant_charging"
            elif instant_charging["limit"]["selected"] == "soc":
                if soc < instant_charging["limit"]["soc"]:
                    return instant_charging["current"], "instant_charging"
                else:
                    return 0, "instant_charging"
            elif instant_charging["limit"]["selected"] == "amount":
                if amount < instant_charging["limit"]["amount"]:
                    return instant_charging["current"], "instant_charging"
                else:
                    return 0, "instant_charging"
        except Exception as e:
            log.exception_logging(e)

    def pv_charging(self, soc):
        """ prüft, ob Min-oder Max-Soc erreicht wurden und setzt entsprechend den Ladestrom.

        Parameter
        ---------
        soc: int
            SoC des EV

        Return
        ------
        Required Current, Chargemode: int, str
            Therotisch benötigter Strom, Ladmodus(soll geladen werden, auch wenn kein PV-Strom zur Verfügung steht)
        """
        try:
            pv_charging = self.data["chargemode"]["pv_charging"]
            if soc < pv_charging["max_soc"]:
                if pv_charging["min_soc"] != 0:
                    if soc < pv_charging["min_soc"]:
                        return pv_charging["min_soc_current"], "instant_charging"
                    else:
                        return pv_charging["min_current"], "pv_charging"
                else:
                    if pv_charging["min_current"] == 0:
                        return 0, "pv_charging"  # nur PV
                    else:
                        return pv_charging["min_current"], "pv_charging"  # Min PV
            else:
                return 0, "stop"
        except Exception as e:
            log.exception_logging(e)

    def scheduled_charging(self, soc, max_current, battery_capacity, max_phases):
        """ prüft, ob der Ziel-SoC erreicht wurde und stellt den zur Erreichung nötigen Ladestrom ein.

        Parameter
        ---------
            soc: int
                Akkustand

            max_current: int
                maximaler Ladestrom

            battery_capacity: float
                Akkugröße

            max_phases: int
                maximale Anzahl Phasen, mit denen das EV laden kann.

        Return
        ------
            Required Current, Chargemode: int, str
                Therotisch benötigter Strom, Ladmodus(soll geladen werden, auch wenn kein PV-Strom zur Verfügung steht)
        """
        for plan in self.data["chargemode"]["scheduled_charging"]:
            if self.data["chargemode"]["scheduled_charging"][plan]["active"] == True:
                try:
                    if soc < self.data["chargemode"]["scheduled_charging"][plan]["soc"]:
                        phases_scheduled_charging = data.general_data["general"].get_phases_chargemode(
                            "scheduled_charging")
                        if max_phases <= phases_scheduled_charging:
                            usable_phases = max_phases
                        else:
                            usable_phases = phases_scheduled_charging

                        available_current = 0.8*max_current*usable_phases
                        required_wh = (
                            (self.data["chargemode"]["scheduled_charging"][plan]["soc"] - soc)/100) * battery_capacity*1000
                        duration = required_wh/(available_current*230)
                        start, remaining_time = timecheck.check_duration(
                            self.data["chargemode"]["scheduled_charging"][plan], duration)
                        if start == 1:
                            return available_current, "instant_charging"
                        elif start == 2:  # weniger als die berechnete Zeit verfügbar
                            return required_wh/(remaining_time*230)
                        else:
                            if timecheck.check_timeframe(self.data["chargemode"]["scheduled_charging"][plan], 24) == True:
                                if data.optional_data["optional"].data["et"]["active"] == True:
                                    hourlist = data.optional_data["optional"].get_loading_hours(
                                        duration)
                                    if timecheck.is_list_valid(hourlist) == True:
                                        return available_current, "instant_charging"
                                    else:
                                        return 0, "pv_charging"
                                else:
                                    return 0, "pv_charging"
                            else:
                                return 0, "scheduled_charging"
                    else:
                        return 0, "stop"
                except Exception as e:
                    log.exception_logging(e)
        else:
            # log
            print("Keine aktiven Zeit-Pläne.")
            return 0, "scheduled_charging"

    def standby(self):
        """ setzt den benötigten Strom auf 0.

        Return
        ------
            Required Current, Chargemode: int, str
                Therotisch benötigter Strom, Ladmodus
        """
        return 0, "standby"
