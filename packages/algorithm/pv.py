"""PV-Logik
Die Leistung, die die PV-Module liefern, kann nicht komplett für das Laden und Smarthome verwendet werden. 
Davon ab geht z.B. noch der Hausverbrauch. Für das Laden mit PV kann deshalb nur der Strom verwendet werden, 
der sonst in das Netz eingespeist werden würde. 
"""

from . import algorithm
from . import data
from ..helpermodules import log
from ..helpermodules import pub
from ..helpermodules import timecheck


class pvAll:
    """
    """

    def __init__(self):
        self.data = {
            "set": {"overhang_power_left": 0,
                    "available_power": 0},
            "get": {"power": 0},
            "config": {"configured": False}}
        self.reset_pv_data()

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
            if len(data.data.pv_data) > 1:
                # Summe von allen konfigurierten Modulen
                self.data["get"]["counter"] = 0
                self.data["get"]["daily_yield"] = 0
                self.data["get"]["monthly_yield"] = 0
                self.data["get"]["yearly_yield"] = 0
                self.data["get"]["power"] = 0
                for module in data.data.pv_data:
                    try:
                        if "pv" in module:
                            self.data["get"]["counter"] += data.data.pv_data[module].data["get"]["counter"]
                            self.data["get"]["daily_yield"] += data.data.pv_data[module].data["get"]["daily_yield"]
                            self.data["get"]["monthly_yield"] += data.data.pv_data[module].data["get"]["monthly_yield"]
                            self.data["get"]["yearly_yield"] += data.data.pv_data[module].data["get"]["yearly_yield"]
                            self.data["get"]["power"] += data.data.pv_data[module].data["get"]["power"]
                    except Exception as e:
                        log.MainLogger().exception("Fehler im allgemeinen PV-Modul fuer "+str(module))
                # Alle Summentopics im Dict publishen
                {pub.pub("openWB/set/pv/get/"+k, v)for (k, v) in self.data["get"].items()}
                self.data["config"]["configured"] = True
                # aktuelle Leistung an der EVU, enthält die Leistung der Einspeisungsgrenze
                evu_overhang = data.data.counter_data[data.data.counter_data["all"].get_evu_counter()].data["get"]["power_all"] * (-1)

                # Regelmodus
                control_range_low = data.data.general_data["general"].data["chargemode_config"]["pv_charging"]["control_range"][0]
                control_range_high = data.data.general_data["general"].data["chargemode_config"]["pv_charging"]["control_range"][1]
                control_range_center = control_range_high - (control_range_high - control_range_low) / 2
                if control_range_low < evu_overhang < control_range_high:
                    available_power = 0
                else:
                    available_power = evu_overhang - control_range_center

                self.data["set"]["overhang_power_left"] = available_power
                log.MainLogger().debug(str(self.data["set"]["overhang_power_left"])+"W EVU-Ueberschuss, der fuer die Regelung verfuegbar ist, davon " +
                                       str(self.data["set"]["reserved_evu_overhang"])+"W fuer die Einschaltverzoegerung reservierte Leistung.")
            # nur allgemeiner PV-Key vorhanden, d.h. kein Modul konfiguriert
            else:
                self.data["config"]["configured"] = False
                available_power = 0
                log.MainLogger().debug("Kein PV-Modul konfiguriert.")
                self.data["set"]["overhang_power_left"] = 0
            self.data["set"]["available_power"] = available_power
            pub.pub("openWB/set/pv/set/available_power", available_power)
            pub.pub("openWB/set/pv/config/configured", self.data["config"]["configured"])
        except Exception as e:
            log.MainLogger().exception("Fehler im allgemeinen PV-Modul")

    def switch_on(self, chargepoint, required_power, required_current, phases, bat_overhang):
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
        required_current: float
            Stromstärke, mit der geladen werden kann
        threshold_not_reached: bool
            True, wenn die Einschaltschwelle nicht erreicht wurde.
        """
        try:
            threshold_not_reached = False
            pv_config = data.data.general_data["general"].data["chargemode_config"]["pv_charging"]
            control_parameter = chargepoint.data["set"]["charging_ev_data"].data["control_parameter"]
            # verbleibender EVU-Überschuss unter Berücksichtigung der Einspeisungsgrenze
            all_overhang = self.overhang_left()
            # Berücksichtigung der Speicherleistung
            all_overhang += bat_overhang
            if chargepoint.data["set"]["charging_ev_data"].ev_template.data["prevent_switch_stop"] == False or max(chargepoint.data["get"]["current"]) == 0:
                if control_parameter["timestamp_switch_on_off"] != "0":
                    # Wurde die Einschaltschwelle erreicht? Reservierte Leistung aus all_overhang rausrechnen,
                    # da diese Leistung ja schon reserviert wurde, als die Einschaltschwelle erreicht wurde.
                    if ((chargepoint.data["set"]["charging_ev_data"].charge_template.data["chargemode"]["pv_charging"]["feed_in_limit"] == False and
                            all_overhang + required_power > pv_config["switch_on_threshold"]*phases) or
                            (chargepoint.data["set"]["charging_ev_data"].charge_template.data["chargemode"]["pv_charging"]["feed_in_limit"] == True and
                             all_overhang + required_power >= data.data.general_data["general"].data["chargemode_config"]["pv_charging"]["feed_in_yield"])):
                        # Timer ist noch nicht abglaufen
                        if timecheck.check_timestamp(control_parameter["timestamp_switch_on_off"], pv_config["switch_on_delay"]) == True:
                            required_power = 0
                            chargepoint.data["get"]["state_str"] = "Die Ladung wird gestartet, sobald nach "+str(pv_config["switch_on_delay"]) + "s die Einschaltverzoegerung abgelaufen ist."
                        # Timer abgelaufen
                        else:
                            control_parameter["timestamp_switch_on_off"] = "0"
                            self.data["set"]["reserved_evu_overhang"] -= pv_config["switch_on_threshold"]*phases
                            log.MainLogger().info("Einschaltschwelle von "+str(pv_config["switch_on_threshold"]) + "W fuer die Dauer der Einschaltverzoegerung ueberschritten.")
                            pub.pub("openWB/set/vehicle/"+str(chargepoint.data["set"]["charging_ev_data"].ev_num)+"/control_parameter/timestamp_switch_on_off", "0")
                    # Einschaltschwelle wurde unterschritten, Timer zurücksetzen
                    else:
                        control_parameter["timestamp_switch_on_off"] = "0"
                        self.data["set"]["reserved_evu_overhang"] -= pv_config["switch_on_threshold"]*phases
                        required_power = 0
                        message = "Einschaltschwelle von "+str(pv_config["switch_on_threshold"]) + "W waehrend der Einschaltverzoegerung unterschritten."
                        log.MainLogger().info("LP "+str(chargepoint.cp_num)+": "+message)
                        chargepoint.data["get"]["state_str"] = message
                        pub.pub("openWB/set/vehicle/"+str(chargepoint.data["set"]["charging_ev_data"].ev_num)+"/control_parameter/timestamp_switch_on_off", "0")
                        threshold_not_reached = True
                else:
                    # Timer starten
                    if ((chargepoint.data["set"]["charging_ev_data"].charge_template.data["chargemode"]["pv_charging"]["feed_in_limit"] == False and
                            all_overhang > pv_config["switch_on_threshold"]*phases) or
                            (chargepoint.data["set"]["charging_ev_data"].charge_template.data["chargemode"]["pv_charging"]["feed_in_limit"] == True and
                             all_overhang >= data.data.general_data["general"].data["chargemode_config"]["pv_charging"]["feed_in_yield"] and
                             self.data["set"]["reserved_evu_overhang"] == 0)):
                        control_parameter["timestamp_switch_on_off"] = timecheck.create_timestamp()
                        self.data["set"]["reserved_evu_overhang"] += pv_config["switch_on_threshold"]*phases
                        required_power = 0
                        message = "Die Ladung wird gestartet, sobald nach "+str(pv_config["switch_on_delay"]) + "s die Einschaltverzoegerung abgelaufen ist."
                        log.MainLogger().info("LP "+str(chargepoint.cp_num)+": "+message)
                        chargepoint.data["get"]["state_str"] = message
                        pub.pub("openWB/set/vehicle/"+str(chargepoint.data["set"]["charging_ev_data"].ev_num)+"/control_parameter/timestamp_switch_on_off", control_parameter["timestamp_switch_on_off"])
                    else:
                        # Einschaltschwelle nicht erreicht
                        message = "Die Ladung kann nicht gestartet werden, da die Einschaltschwelle ("+str(pv_config["switch_on_threshold"])+"W) nicht erreicht wird."
                        log.MainLogger().info("LP "+str(chargepoint.cp_num)+": "+message)
                        if chargepoint.data["get"]["state_str"] is None:
                            chargepoint.data["get"]["state_str"] = message
                        required_power = 0
                        threshold_not_reached = True
            else:
                chargepoint.data["get"]["state_str"] = "Die Ladung wurde aufgrund des EV-Profils ohne Einschaltverzögerung gestartet, um die Ladung nicht zu unterbrechen."

            if required_power != 0:
                required_current, _ = algorithm.allocate_power(chargepoint, required_power, required_current, phases)
            else:
                required_current = 0
            return required_current, threshold_not_reached
        except Exception as e:
            log.MainLogger().exception("Fehler im allgemeinen PV-Modul")
            return 0, phases

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
            pv_config = data.data.general_data["general"].data["chargemode_config"]["pv_charging"]
            control_parameter = chargepoint.data["set"]["charging_ev_data"].data["control_parameter"]

            if control_parameter["timestamp_switch_on_off"] != "0":
                if timecheck.check_timestamp(control_parameter["timestamp_switch_on_off"], pv_config["switch_off_delay"]) == False:
                    control_parameter["timestamp_switch_on_off"] = "0"
                    self.data["set"]["released_evu_overhang"] -= chargepoint.data["set"]["required_power"]
                    message = "Ladevorgang nach Ablauf der Abschaltverzoegerung gestoppt."
                    log.MainLogger().info("LP "+str(chargepoint.cp_num)+": "+message)
                    chargepoint.data["get"]["state_str"] = message
                    pub.pub("openWB/set/vehicle/"+str(chargepoint.data["set"]["charging_ev_data"].ev_num)+"/control_parameter/timestamp_switch_on_off", "0")
                    return True
                else:
                    chargepoint.data["get"]["state_str"] = "Ladevorgang wird nach Ablauf der Abschaltverzoegerung (" + str(pv_config["switch_off_delay"])+"s) gestoppt."
            return False
        except Exception as e:
            log.MainLogger().exception("Fehler im allgemeinen PV-Modul")
            return False

    def switch_off_check_threshold(self, chargepoint, overhang):
        """ prüft, ob die Abschaltschwelle erreicht wurde und startet die Abschaltverzögerung. 
        Ist die Abschaltverzögerung bereits aktiv, wird geprüft, ob die Abschaltschwelle wieder 
        unterschritten wurde, sodass die Verzögerung wieder gestoppt wird.

        Parameter
        ---------
        chargepoint: dict
            Daten des Ladepunkts
        """
        try:

            control_parameter = chargepoint.data["set"]["charging_ev_data"].data["control_parameter"]
            pv_config = data.data.general_data["general"].data["chargemode_config"]["pv_charging"]
            # Der EVU-Überschuss muss ggf um die Einspeisungsgrenze bereinigt werden.
            if chargepoint.data["set"]["charging_ev_data"].charge_template.data["chargemode"]["pv_charging"]["feed_in_limit"] == True:
                feed_in_yield = data.data.general_data["general"].data["chargemode_config"]["pv_charging"]["feed_in_yield"]
            else:
                feed_in_yield = 0
            if control_parameter["timestamp_switch_on_off"] != "0":
                # Wurde die Abschaltschwelle erreicht?
                # Eigene Leistung aus der freigegebenen Leistung rausrechnen.
                if (overhang + self.data["set"]["released_evu_overhang"] - chargepoint.data["set"]["required_power"]) > (pv_config["switch_off_threshold"]*-1 + feed_in_yield):
                    control_parameter["timestamp_switch_on_off"] = "0"
                    self.data["set"]["released_evu_overhang"] -= chargepoint.data["set"]["required_power"]
                    log.MainLogger().info("Abschaltschwelle während der Verzögerung ueberschritten.")
                    pub.pub("openWB/set/vehicle/"+str(chargepoint.data["set"]["charging_ev_data"].ev_num)+"/control_parameter/timestamp_switch_on_off", "0")
            else:
                # Wurde die Abschaltschwelle ggf. durch die Verzögerung anderer LP erreicht?
                if (overhang + self.data["set"]["released_evu_overhang"]) < (pv_config["switch_off_threshold"]*-1 + feed_in_yield):
                    if chargepoint.data["set"]["charging_ev_data"].ev_template.data["prevent_switch_stop"] == False:
                        control_parameter["timestamp_switch_on_off"] = timecheck.create_timestamp()
                        # merken, dass ein LP verzögert wird, damit nicht zu viele LP verzögert werden.
                        self.data["set"]["released_evu_overhang"] += chargepoint.data["set"]["required_power"]
                        message = "Ladevorgang wird nach Ablauf der Abschaltverzoegerung (" + str(pv_config["switch_off_delay"])+"s) gestoppt."
                        log.MainLogger().info("LP "+str(chargepoint.cp_num)+": "+message)
                        chargepoint.data["get"]["state_str"] = message
                        pub.pub("openWB/set/vehicle/"+str(chargepoint.data["set"]["charging_ev_data"].ev_num)+"/control_parameter/timestamp_switch_on_off", control_parameter["timestamp_switch_on_off"])
                        # Die Abschaltvschwelle wird immer noch überschritten und es sollten weitere LP abgeschaltet werden.
                    else:
                        chargepoint.data["get"]["state_str"] = "Stoppen des Ladevorgangs aufgrund des EV-Profils verhindert."
        except Exception as e:
            log.MainLogger().exception("Fehler im allgemeinen PV-Modul")

    def reset_switch_on_off(self, chargepoint, charging_ev):
        """ Zeitstempel und reseervierte Leistung löschen

        Parameter
        ---------
        chargepoint: dict
            Ladepunkt, für den die Werte zurückgesetzt werden sollen
        charging_ev: dict
            EV, das dem Ladepunkt zugeordnet ist
        """
        try:
            if charging_ev.data["control_parameter"]["timestamp_switch_on_off"] != "0":
                charging_ev.data["control_parameter"]["timestamp_switch_on_off"] = "0"
                pub.pub("openWB/set/vehicle/"+str(charging_ev.ev_num)+"/control_parameter/timestamp_switch_on_off", "0")
                # Wenn bereits geladen wird, freigegebene Leistung freigeben. Wenn nicht geladen wird, reservierte Leistung freigeben.
                pv_config = data.data.general_data["general"].data["chargemode_config"]["pv_charging"]
                if chargepoint.data["get"]["charge_state"] == False:
                    data.data.pv_data["all"].data["set"]["reserved_evu_overhang"] -= pv_config["switch_on_threshold"]*chargepoint.data["set"]["phases_to_use"]
                    log.MainLogger().debug("reserved_evu_overhang 10 "+str(data.data.pv_data["all"].data["set"]["reserved_evu_overhang"]))
                else:
                    data.data.pv_data["all"].data["set"]["released_evu_overhang"] -= pv_config["switch_on_threshold"]*charging_ev.data["control_parameter"]["phases"]
                    log.MainLogger().debug("reserved_evu_overhang 11 "+str(data.data.pv_data["all"].data["set"]["reserved_evu_overhang"]))
        except Exception as e:
            log.MainLogger().exception("Fehler im allgemeinen PV-Modul")

    def overhang_left(self):
        """ gibt den verfügbaren EVU-Überschuss zurück.

        Return
        ------
        overhang_power_left: int
            verfügbarer EVU-Überschuss + bereits genutzter Überschuss
        """
        try:
            if self.data["config"]["configured"] == True:
                return self.data["set"]["overhang_power_left"] - self.data["set"]["reserved_evu_overhang"]
            else:
                return 0
        # return available pv power with feed in yield
        except Exception as e:
            log.MainLogger().exception("Fehler im allgemeinen PV-Modul")
            return 0

    def allocate_evu_power(self, required_power):
        """ subtrahieren der zugeteilten Leistung vom verfügbaren EVU-Überschuss

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
                self.data["set"]["overhang_power_left"] -= required_power
                log.MainLogger().debug(str(self.data["set"]["overhang_power_left"])+"W EVU-Ueberschuss, der fuer die folgenden Ladepunkte uebrig ist, davon " +
                                       str(self.data["set"]["reserved_evu_overhang"])+"W fuer die Einschaltverzoegerung reservierte Leistung.")
                # Float-Ungenauigkeiten abfangen
                if self.data["set"]["overhang_power_left"] < -0.01:
                    # Fehlermeldung nur ausgeben, wenn Leistung allokiert wird.
                    # Es kann nicht immer mit einem LP so viel Leistung freigegeben werden, dass die verfügbare Leistung positiv ist.
                    if required_power > 0:
                        log.MainLogger().error("Es wurde versucht, mehr EVU-Überschuss zu allokieren, als vorhanden ist.")
                    too_much = self.data["set"]["overhang_power_left"]
                    self.data["set"]["overhang_power_left"] = 0
                    return too_much
            return 0
        except Exception as e:
            log.MainLogger().exception("Fehler im allgemeinen PV-Modul")
            return required_power

    def put_stats(self):
        """ Publishen und Loggen des verbleibnden EVU-Überschusses und reservierten Leistung
        """
        try:
            pub.pub("openWB/set/pv/config/configured", self.data["config"]["configured"])
            if self.data["config"]["configured"] == True:
                pub.pub("openWB/set/pv/set/overhang_power_left",   self.data["set"]["overhang_power_left"])
                pub.pub("openWB/set/pv/set/reserved_evu_overhang", self.data["set"]["reserved_evu_overhang"])
                pub.pub("openWB/set/pv/set/released_evu_overhang", self.data["set"]["released_evu_overhang"])
        except Exception as e:
            log.MainLogger().exception("Fehler im allgemeinen PV-Modul")

    def reset_pv_data(self):
        """ setzt die Daten zurück, die über mehrere Regelzyklen genutzt werden.
        """
        try:
            pub.pub("openWB/set/pv/set/reserved_evu_overhang", 0)
            pub.pub("openWB/set/pv/set/released_evu_overhang", 0)
            self.data["set"]["reserved_evu_overhang"] = 0
            self.data["set"]["released_evu_overhang"] = 0
        except Exception as e:
            log.MainLogger().exception("Fehler im allgemeinen PV-Modul")

    def print_stats(self):
        try:
            log.MainLogger().debug(str(self.data["set"]["overhang_power_left"])+"W EVU-Ueberschuss, der fuer die Regelung verfuegbar ist, davon " +
                                   str(self.data["set"]["reserved_evu_overhang"])+"W fuer die Einschaltverzoegerung reservierte Leistung.")
        except Exception as e:
            log.MainLogger().exception("Fehler im allgemeinen PV-Modul")


class pv:

    def __init__(self, index):
        self.data = {}
        self.pv_num = index
        self.data["get"] = {}
        self.data["get"]["daily_yield"] = 0
        self.data["get"]["monthly_yield"] = 0
        self.data["get"]["yearly_yield"] = 0
