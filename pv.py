"""PV-Logik
Die Leistung, die die PV-Module liefern, kann nicht komplett für das Laden und Smarthome verwendet werden. 
Davon ab geht z.B. noch der Hausverbrauch. Für das Laden mit PV kann deshalb nur der Strom verwendet werden, 
der sonst in das Netz eingespeist werden würde. 
"""

import traceback

import data
import loadmanagement
import log
import pub
import timecheck


class pv():
    """
    """

    def __init__(self):
        self.data = {}
        if "set" not in self.data:
            self.data["set"] = {}
        if "get" not in self.data:
            self.data["get"] = {}
        pub.pub("openWB/pv/get/overhang_power_left", 0)
        pub.pub("openWB/pv/get/reserved_pv_power", 0)
        pub.pub("openWB/pv/get/released_pv_power", 0)
        pub.pub("openWB/pv/set/available_power", 0)
        pub.pub("openWB/pv/config/configured", False)

    def calc_power_for_control(self):
        """ berechnet den EVU-Überschuss, der in der Regelung genutzt werden kann.
        Regelmodus: Wenn möglichst der ganze PV-Strom genutzt wird, sollte die EVU-Leistung irgendwo 
            im Bereich um 0 leigen. Um ein Aufschwingen zu vermeiden, sollte die verfügbare Leistung nur 
            angepasst werden, wenn sie außerhalb des Regelbereichs liegt.

        Return
        ------
        int: PV-Leistung, die genutzt werden darf (auf allen Phasen/je Phase unterschiedlich?)
        """
        try:
            if len(data.pv_data) > 1:
                self.data["config"]["configured"]=True
                # aktuelle Leistung an der EVU, enthält die Leistung der Einspeisungsgrenze
                evu_overhang = data.counter_data["evu"].data["get"]["power_all"] * (-1)
                
                if evu_overhang > 0:
                    # Regelmodus
                    control_range_low = self.data["config"]["control_range"][0]
                    control_range_high = self.data["config"]["control_range"][1]
                    control_range_center = (control_range_high - control_range_low) / 2
                    if control_range_low < evu_overhang < control_range_high:
                        available_power = evu_overhang
                    else:
                        available_power = evu_overhang - control_range_center
                else:
                    available_power = 0

                log.message_debug_log("debug", str(available_power)+"W EVU-Ueberschuss, der für die Regelung verfuegbar ist, davon "+str(self.data["get"]["reserved_pv_power"])+"W fuer die Einschaltverzoegerung reservierte Leistung.")
            # nur allgemeiner PV-Key vorhanden, d.h. kein Modul konfiguriert
            else:
                self.data["config"]["configured"]=False
                available_power = 0 # verfügbare Leistung, Regelpunkt ist im Regelintervall
                log.message_debug_log("debug", "Kein PV-Modul konfiguriert.")
            self.data["get"]["overhang_power_left"] = available_power
            self.data["set"]["available_power"] = available_power
            pub.pub("openWB/pv/set/available_power", available_power)
            pub.pub("openWB/pv/config/configured", self.data["config"]["configured"])

        except Exception as e:
            log.exception_logging(e)

    def switch_on(self, chargepoint, required_power, required_current, phases):
        """ prüft, ob die Einschaltschwelle erreicht wurde, reserviert Leistung und gibt diese frei 
        bzw. stoppt die Freigabe wenn die Ausschaltschwelle und -verzögerung erreicht wurde.

        Erst wenn für eine bestimmte Zeit eine bestimmte Grenze über/unter-
        schritten wurde, wird die Ladung gestartet/gestoppt. So wird häufiges starten/stoppen 
        vermieden. Die Grenzen aus den Einstellungen sind als Deltas zu verstehen, die absoluten 
        Schaltpunkte ergeben sich ggf noch aus der Einspeisungsgrenze.

        Parameter
        ---------
        chargepoint: dict
            Daten des Ladepunkts
        required_power: float
            Leistung, mit der geladen werden soll
        required_current: float
            Stromstärke, mit der geladen werden soll
        phases: int
            Phasen, mit denen geladen werden soll
        Return
        ------
        required_power: float
            Leistung, mit der geladen werden kann
        required_current: float
            Stromstärke, mit der geladen werden kann
        phases: int
            Phasen, mit denen geladen werden kann
        """
        try:
            pv_config = self.data["config"]
            control_parameter = chargepoint.data["set"]["charging_ev"].data["control_parameter"]
            # verbleibender EVU-Überschuss unter Berücksichtigung der Einspeisungsgrenze
            overhang_power_left_feed_in = self.power_for_pv_charging(chargepoint.data["set"]["charging_ev"].charge_template.data["chargemode"]["pv_charging"]["feed_in_limit"])
            if  chargepoint.data["get"]["charge_state"] == False:
                if control_parameter["timestamp_switch_on_off"] != False:
                    # Wurde die Einschaltschwelle erreicht?
                    if overhang_power_left_feed_in + required_power > pv_config["switch_on_threshold"]*phases:
                        # Timer ist noch nicht abglaufen
                        if timecheck.check_timestamp(control_parameter["timestamp_switch_on_off"], pv_config["switch_on_delay"]) == True:
                            required_power = 0
                        # Timer abgelaufen
                        else:
                            control_parameter["timestamp_switch_on_off"] = 0
                            self.data["get"]["reserved_pv_power"] -= required_power
                            log.message_debug_log("info", "Einschaltschwelle von "+str(pv_config["switch_on_threshold"])+ "W fuer die Dauer der Einschaltverzoegerung ueberschritten.")
                            pub.pub("openWB/vehicle/"+str(chargepoint.data["set"]["charging_ev"].ev_num)+"/control_parameter/timestamp_switch_on_off",0)
                    # Einschaltschwelle wurde unterschritten, Timer zurücksetzen
                    else:
                        control_parameter["timestamp_switch_on_off"] = 0
                        required_power = 0
                        self.data["get"]["reserved_pv_power"] -= required_power
                        log.message_debug_log("info", "Einschaltschwelle von "+str(pv_config["switch_on_threshold"])+ "W waehrend der Einschaltverzoegerung unterschritten.")
                        pub.pub("openWB/vehicle/"+str(chargepoint.data["set"]["charging_ev"].ev_num)+"/control_parameter/timestamp_switch_on_off", 0)
                else:
                    # Timer starten
                    if overhang_power_left_feed_in > pv_config["switch_on_threshold"]*phases:
                        control_parameter["timestamp_switch_on_off"] = timecheck.create_timestamp()
                        self.data["get"]["reserved_pv_power"] += required_power
                        required_power = 0
                        log.message_debug_log("info", "Einschaltverzoegerung für "+str(pv_config["switch_on_delay"])+ "s aktiv.")
                        pub.pub("openWB/vehicle/"+str(chargepoint.data["set"]["charging_ev"].ev_num)+"/control_parameter/timestamp_switch_on_off", control_parameter["timestamp_switch_on_off"])
                    else:
                        required_power = 0
            # Liegt die Einschaltgrenze unter der benötigten Leistung, muss bezogen werden.
            if required_power != 0:
                if (overhang_power_left_feed_in - required_power) < 0:
                    evu_power = overhang_power_left_feed_in *-1 # muss bezogen werden
                    pv_power = required_power - evu_power
                    evu_current = required_power / (phases * 230)
                    if evu_power > 0:
                        if loadmanagement.loadmanagement(evu_power, evu_current, phases) == False:
                            self.allocate_pv_power(pv_power)
                else:
                    self.allocate_pv_power(required_power)
            else:
                required_current = 0
                phases = 0
            return required_power, required_current, phases
        except Exception as e:
            log.exception_logging(e)

    def switch_off_check_timer(self, chargepoint):
        """ prüft, ob der Timer der Ausschaltverzögerung abgelaufen ist.

        Parameter
        ---------
        chargepoint: dict
            Daten des Ladepunkts

        Return
        ------
        True: Timer abgelaufen
        False: Timer noch nicht abgelaufen
        """
        try:
            pv_config = self.data["config"]
            control_parameter = chargepoint.data["set"]["charging_ev"].data["control_parameter"]

            if control_parameter["timestamp_switch_on_off"] != False:
                if timecheck.check_timestamp(control_parameter["timestamp_switch_on_off"], pv_config["switch_off_delay"]) == False:
                    control_parameter["timestamp_switch_on_off"] = 0
                    self.data["get"]["released_pv_power"] -= chargepoint.data["set"]["current"]*chargepoint.data["set"]["phases_to_use"]*230
                    log.message_debug_log("info", "Abschaltschwelle von "+str(pv_config["switch_off_threshold"])+"W fuer die Dauer der Abschaltverzöegerung unterschritten.")
                    pub.pub("openWB/vehicle/"+str(chargepoint.data["set"]["charging_ev"].ev_num)+"/control_parameter/timestamp_switch_on_off",0)
                    return True
            return False
        except Exception as e:
            log.exception_logging(e)

    def switch_off_check_threshold(self, chargepoint):
        """ prüft, ob die Abschaltschwelle erreicht wurde und startet die Abschaltverzögerung. 
        Ist die Abschaltverzögerung bereits aktiv, wird geprüft, ob die Abschaltschwelle wieder 
        unterschritten wurde, sodass die Verzögerung wieder gestoppt wird.

        Parameter
        ---------
        chargepoint: dict
            Daten des Ladepunkts

        Return
        ------
        True: Es muss noch mehr Leistung freigegeben werden.
        False: Es wurde genügend Leistung freigegeben.
        """
        try:
            control_parameter = chargepoint.data["set"]["charging_ev"].data["control_parameter"] 
            pv_config = self.data["config"]
            # Der EVU-Überschuss muss ggf um die Einspeisungsgrenze bereinigt werden.
            if chargepoint.data["set"]["charging_ev"].charge_template.data["chargemode"]["pv_charging"]["feed_in_limit"] == True:
                feed_in_limit = self.data["config"]["feed_in_yield"]
            else:
                feed_in_limit = 0
            if control_parameter["timestamp_switch_on_off"] != False:
                # Wurde die Abschaltschwelle erreicht?
                if (data.counter_data["evu"].data["get"]["power_all"] + feed_in_limit) < pv_config["switch_off_threshold"]:
                    # Wurden bereits bei so vielen LP die Abschaltverzögerung abgebrochen, dass die Abschaltschwelle nicht mehr überschritten wird? 
                    # Wenn nein, dann stoppe bei einem weiteren Ladepunkt die Abschaltverzögerung.
                    if (data.counter_data["evu"].data["get"]["power_all"]- feed_in_limit - self.data["get"]["released_pv_power"]) > pv_config["switch_off_threshold"]:
                        control_parameter["timestamp_switch_on_off"] = 0
                        self.data["get"]["released_pv_power"] -= chargepoint.data["set"]["current"]*chargepoint.data["set"]["phases_to_use"]*230
                        log.message_debug_log("info", "Abschaltschwelle während der Verzögerung unterschritten.")
                        pub.pub("openWB/vehicle/"+str(chargepoint.data["set"]["charging_ev"].ev_num)+"/control_parameter/timestamp_switch_on_off", 0)
            else:
                # Wurde die Abschaltschwelle ggf. durch die Verzögerung anderer LP erreicht?
                if (data.counter_data["evu"].data["get"]["power_all"] + feed_in_limit - self.data["get"]["released_pv_power"]) > pv_config["switch_off_threshold"]:
                    control_parameter["timestamp_switch_on_off"] = timecheck.create_timestamp()
                    # merken, dass ein LP verzögert wird, damit nicht zu viele LP verzögert werden.
                    self.data["get"]["released_pv_power"] += chargepoint.data["set"]["current"]*chargepoint.data["set"]["phases_to_use"]*230
                    log.message_debug_log("info", "Abschaltverzögerung für "+ str(pv_config["switch_off_delay"])+"s aktiv.")
                    pub.pub("openWB/vehicle/"+str(chargepoint.data["set"]["charging_ev"].ev_num)+"/control_parameter/timestamp_switch_on_off", control_parameter["timestamp_switch_on_off"])
                    # Die Abschaltvschwelle wird immer noch überschritten und es sollten weitere LP abgeschaltet werden.
            if (data.counter_data["evu"].data["get"]["power_all"] + feed_in_limit - self.data["get"]["released_pv_power"]) > pv_config["switch_off_threshold"]:
                return True
            else:
                return False
        except Exception as e:
            log.exception_logging(e)

    def power_for_pv_charging(self, feed_in_yield_active):
        """ gibt den verfügbaren EVU-Überschuss unter Berücksichtigung der Einspeisungsgrenze zurück.

        Einspeisungsgrenze: Meist darf nur bis zu einem bestimmten Ertrag eingespeist werden (70%). 
            Bei einem guten Ertrag wird dann nur der PV-Strom genutzt, der nicht ins Netz eingespeist 
            werden darf.

        Paramter
        --------
        feed_in_limit_active: bool
            Soll die Einspeisungsgrenze berücksichtigt werden?

        Return
        ------
        overhang_power_left: int
            verfügbarer EVU-Überschuss + bereits genutzter Überschuss
        """
        try:
            if self.data["config"]["configured"] == True:
                # Einspeisungsgrenze (Verschiebung des Regelpunkts)
                if feed_in_yield_active == True:
                    remaining_power = self.data["get"]["overhang_power_left"] - self.data["get"]["reserved_pv_power"] - self.data["config"]["feed_in_yield"]
                    if remaining_power > 0:
                        return remaining_power
                    else:
                        return 0
                else:
                    return self.data["get"]["overhang_power_left"]

            else:
                log.message_debug_log("warning", "PV-Laden aktiv, obwohl kein PV-Modul konfiguriert wurde.")
                return 0
        # return available pv power with feed in yield
        except Exception as e:
                log.exception_logging(e)

    def power_for_normal_load(self):
        """ gibt den verfügbaren EVU-Überschuss zurück.

        Return
        ------
        overhang_power_left: int
            verfügbare PV-Leistung
        """
        try:
            if self.data["config"]["configured"] == True:
                return (self.data["get"]["overhang_power_left"] - self.data["get"]["reserved_pv_power"])
            else:
                return 0
        # return available pv power without feed in yield
        except Exception as e:
                log.exception_logging(e)

    def allocate_pv_power(self, required_power):
        """ subtrahieren der zugeteilten Leistung vomverfügbaren EVU-Überschuss

        Parameter
        ---------
        required_power: float
            Leistung, mit der geladen werden soll
        """
        try:
            if self.data["config"]["configured"] == True:
                self.data["get"]["overhang_power_left"] -= required_power
                log.message_debug_log("debug", str(self.data["get"]["overhang_power_left"])+"W EVU-Ueberschuss, der fuer die folgenden Ladepunkte uebrig ist, davon "+str(self.data["get"]["reserved_pv_power"])+"W fuer die Einschaltverzoegerung reservierte Leistung.")
                if self.data["get"]["overhang_power_left"] < 0:
                    pass #error
        except Exception as e:
            log.exception_logging(e)

    def put_stats(self):
        """ Publishen und Loggen des verbleibnden EVU-Überschusses und reservierten Leistung
        """
        try:
            pub.pub("openWB/pv/config/configured", self.data["config"]["configured"])
            if self.data["config"]["configured"] == True:
                pub.pub("openWB/pv/get/overhang_power_left", self.data["get"]["overhang_power_left"])
                pub.pub("openWB/pv/get/reserved_pv_power", self.data["get"]["reserved_pv_power"])
                pub.pub("openWB/pv/get/released_pv_power", self.data["get"]["released_pv_power"])
        except Exception as e:
            log.exception_logging(e)


class pvModule():
    """
    """

    def __init__(self):
        self.data = {}
    """
    """
