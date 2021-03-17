""" Algrithmus zur Berechnung der Ladeströme
"""

import data
import loadmanagement
import log
import pub
import timecheck


class control():
    """Verteilung des Stroms auf die Ladepunkte
    """

    def __init__(self):
        pass

    def calc_current(self):
        """ Einstiegspunkt in den Regel-Algorithmus
        ruft in der Reihenfolge der Prioritäten der Lademodi die Berechnungsfunktion auf.
        """
        if data.counter_data["evu"].data["set"]["consumption_left"] > 0:
            # Überschuss für Ladepunkte verwenden, die noch nicht laden
            self._calc_cp_in_specified_mode("scheduled_load", "instant_load")
            self._calc_cp_in_specified_mode(None, "time_load")
            self._calc_cp_in_specified_mode("instant_load", "instant_load")
            self._calc_cp_in_specified_mode("pv_load", "instant_load")
            self._calc_cp_in_specified_mode("scheduled_load", "pv_load")
            self._calc_cp_in_specified_mode("pv_load", "pv_load")
            self._calc_cp_in_specified_mode(None, "standby")
            self._calc_cp_in_specified_mode(None, "stop")

            # Übrigen Überschuss auf Ladepunkte im PV-Modus verteilen
            #self.distribute_unsued_evu_overhang()
        else:
            #Ist jetzt schon die Sicherung geflogen?
            log.message_debug_log("warning", "Verwendete Leistung überschreitet den zulässigen Bezug um "+str((data.counter_data["evu"].data["set"]["consumption_left"]*-1))+"W.")
            # todo LP abschalten

        self._start_charging()

    def _calc_cp_in_specified_mode(self, mode, submode):
        """ ermittelt die Ladepunkte, bei denen der angebenene Lademodus und der Lademodus, 
        der aufgrund des Zustands des eingestellten Lademodus benötigt wird, aktiv sind. Zuerst für die Lade-
        punkte mit Priorität, dann für die Ladepunkte ohne Priorität.

        Parameter
        ---------
        mode: str
            Lademodus, der am Ladepunkt eingestellt ist

        submode: str
            Lademodus, der aufgrund des Zustands des eingestellten Lademodus benötigt wird
        """
        
        try:
            while True:
                preferenced_chargepoint = None
                valid_chargepoints = {}
                for cp in data.cp_data:
                    if "cp" in cp:
                        chargepoint = data.cp_data[cp]
                        if "current" in chargepoint.data["set"]:
                            if chargepoint.data["set"]["current"] != 0:
                                continue
                        if "charging_ev" in chargepoint.data["set"]:
                            charging_ev = chargepoint.data["set"]["charging_ev"]
                            if mode == None:
                                if(charging_ev.charge_template.data["prio"] == True) and (charging_ev.data["control_parameter"]["chargemode"] == submode):
                                    valid_chargepoints[chargepoint] = None
                            elif (charging_ev.charge_template.data["prio"] == True) and (charging_ev.charge_template.data["chargemode"]["selected"] == mode) and (charging_ev.data["control_parameter"]["chargemode"] == submode):
                                valid_chargepoints[chargepoint] = None
                preferenced_chargepoint = self._get_preferenced_chargepoint(valid_chargepoints)

                # Es gibt keine Ladepunkte mit Priorität in diesem Lademodus, die noch nicht laden, daher Ladepunkte ohne Priorität prüfen.
                if preferenced_chargepoint == None:
                    for cp in data.cp_data:
                        if "cp" in cp:
                            chargepoint = data.cp_data[cp]
                            if "charge_state" in chargepoint.data["get"]:
                                if chargepoint.data["get"]["charge_state"] == True:
                                    continue
                            if "charging_ev" in chargepoint.data["set"]:
                                charging_ev = chargepoint.data["set"]["charging_ev"]
                                if mode == None:
                                    if(charging_ev.charge_template.data["prio"] == False) and (charging_ev.data["control_parameter"]["chargemode"] == submode):
                                        valid_chargepoints[chargepoint] = None
                                elif (charging_ev.charge_template.data["prio"] == False) and (charging_ev.charge_template.data["chargemode"]["selected"] == mode) and (charging_ev.data["control_parameter"]["chargemode"] == submode):
                                    valid_chargepoints[chargepoint] = None
                    preferenced_chargepoint = self._get_preferenced_chargepoint(valid_chargepoints)

                if preferenced_chargepoint == None:
                    # Es gibt keine Ladepunkte in diesem Lademodus, die noch nicht laden
                    break
                else:
                    self._start_indiviual_calc(preferenced_chargepoint)
        except Exception as e:
            log.exception_logging(e)

    
    def _get_preferenced_chargepoint(self, valid_chargepoints):
        """ermittelt aus dem Dictionary den Ladepunkt, der eindeutig die Bedingung erfüllt. Die Bedingungen sind:
        geringste Mindeststromstärke, niedrigster SoC, frühester Ansteck-Zeitpunkt, niedrigste Ladepunktnummer.
        Parameter
        ---------
        valid_chargepoints: dict
            enthält alle Ladepunkte gleicher Priorität und Lademodus, die noch nicht laden oder eine Zuteilung haben.

        Return
        ------
        preferenced_chargepoint: dict
            Ladepunkt, der vorrangig geladen werden soll
        """
        preferenced_chargepoint = None
        condition_types = ("min_current", "soc", "plug_in", "cp_num") # Bedingungen in der Reihenfolge, in der sie geprüft werden.
        condition = 0
        if len(valid_chargepoints) > 0:
            while (preferenced_chargepoint == None and (condition <= 3)):
                # entsprechend der Bedingung die Values im Dictionary füllen
                if condition_types[condition] == "min_current":
                    valid_chargepoints.update((cp, cp.data["set"]["charging_ev"].data["control_parameter"]["required_current"]) for cp, val in valid_chargepoints.items())
                elif condition_types[condition] == "soc":
                    valid_chargepoints.update((cp, cp.data["set"]["charging_ev"].data["get"]["soc"]) for cp, val in valid_chargepoints.items())
                elif condition_types[condition] == "plug_in":
                    valid_chargepoints.update((cp, cp.data["get"]["plug_time"]) for cp, val in valid_chargepoints.items())
                else:
                    valid_chargepoints.update((cp, cp.cp_num) for cp, val in valid_chargepoints.items())

                print(valid_chargepoints)
                min_value = min(valid_chargepoints.values())
                min_cp = [key for key in valid_chargepoints if valid_chargepoints[key] == min_value]
                if len(min_cp) > 1:
                    # Wenn es mehrere LP gibt, die den gleichen Minimalwert haben, nächste Bedingung prüfen.
                    condition += 1
                else:
                    preferenced_chargepoint = min_cp[0]

        return preferenced_chargepoint

    def _start_indiviual_calc(self, chargepoint):
        """ ermittelt die konfigurierte Anzahl Phasen, Stromstärke und Leistung.

        Parameter
        ---------
        chargepoint: dict
            Daten des Ladepunkts
        Return
        ------
        """
        try:
            charging_ev = chargepoint.data["set"]["charging_ev"]
            phases = self._get_phases(chargepoint)
            required_current = charging_ev.data["control_parameter"]["required_current"]
            required_power = phases * 230 * \
                charging_ev.data["control_parameter"]["required_current"]
            if charging_ev.data["control_parameter"]["chargemode"] == "pv_load":
                self._calc_pv_load(chargepoint, required_power,
                                required_current, phases)
            elif (charging_ev.data["control_parameter"]["chargemode"] == "stop" or (charging_ev.data["control_parameter"]["chargemode"] == "standby")):
                required_power, required_current, phases = self._no_load()
                self._process_data(chargepoint, required_power, required_current, phases)
            else:
                self._calc_normal_load(chargepoint, required_power,
                                    required_current, phases)
        except Exception as e:
            log.exception_logging(e)

    def _calc_normal_load(self, chargepoint, required_power, required_current, phases):
        """ prüft, ob mit PV geladen werden kann oder bezogen werden muss.

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
        """
        try:
            # PV-Strom nutzen
            overhang_power_left = data.pv_data["pv"].power_for_normal_load()
            if overhang_power_left > 0:
                overhang_power_left -= required_power
                if overhang_power_left > 0:
                    data.pv_data["pv"].allocate_pv_power(required_power)
                    self._process_data(chargepoint, required_power, required_current, phases)
                else:
                    evu_power = overhang_power_left *-1 # muss bezogen werden
                    pv_power = required_power - evu_power
                    evu_current = required_power / (phases * 230)
                    if loadmanagement.loadmanagement(evu_power, evu_current, phases) == True:
                        data.pv_data["pv"].allocate_pv_power(pv_power)
                    else:
                        required_power, required_current, phases= self._no_load()
                    self._process_data(chargepoint, required_power, required_current, phases)
                return
            # Bezug
            if loadmanagement.loadmanagement(required_power, required_current, phases) != True:
                 required_power, required_current, phases= self._no_load()
            self._process_data(chargepoint, required_power, required_current, phases)
        except Exception as e:
            log.exception_logging(e)

    def _calc_pv_load(self, chargepoint, required_power, required_current, phases):
        """prüft, ob Speicher oder EV Vorrang hat und wie viel Strom/Leistung genutzt werden kann.

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
        """
        try:
            overhang_power_left = data.pv_data["pv"].power_for_pv_load(chargepoint.data["set"]["charging_ev"].charge_template.data["chargemode"]["pv_load"]["feed_in_limit"])
            if overhang_power_left > 0:
                # # prüfen, dass es in den letzten 10s nicht über dem Minimum/unter dem Maximum lag
                # chargepoint.data["set"]["charging_ev"].phase_switch_stop_timer(chargepoint)
                # # prüfen, ob Timer abgelaufen ist
                # phases = chargepoint.data["set"]["charging_ev"].check_phase_switch_switching(chargepoint)
                bat_charging_power_left = data.bat_module_data["bat"].power_for_bat_charging()
                if chargepoint.data["set"]["charging_ev"].charge_template.data["chargemode"]["selected"] == "scheduled_load" and "pv_load" not in chargepoint.data["set"]["charging_ev"].charge_template.data["chargemode"]:
                    required_power, required_current, phases = self._no_load()
                    log.message_debug_log("warning", "PV-Laden im Modus Zielladen aktiv und es wurden keine Einstellungen für PV-Laden konfiguriert.")
                else:
                    # EV hat Vorrang
                    if (chargepoint.data["set"]["charging_ev"].charge_template.data["chargemode"]["pv_load"]["bat_prio"] == False) and (bat_charging_power_left > 0):
                        # Laden nur mit der Leistung, die vorher der Speicher bezogen hat
                        if ( bat_charging_power_left - required_power) > 0:
                            data.bat_module_data["bat"].allocate_bat_power(required_power )
                        # Laden mit PV-Leistung und der Leistung, die vorher der Speicher bezogen hat
                        elif overhang_power_left > 0:
                            pv_power = required_power - bat_charging_power_left
                            required_power, required_current, phases = data.pv_data["pv"].switch_on_off(chargepoint, pv_power, required_current, phases)
                            data.bat_module_data["bat"].allocate_bat_power(bat_charging_power_left )
                        else:
                            # keine Leistung übrig
                            required_power, required_current, phases = self._no_load()
                    # Speicher hat Vorrang, aber es wird noch eingespeist
                    elif overhang_power_left > 0:
                        required_power, required_current, phases = data.pv_data["pv"].switch_on_off(chargepoint, required_power, required_current, phases)
                    else:
                        # Speicher zieht gesamte PV-Leistung und hat Vorrang -> keine Ladung
                        required_power, required_current, phases = self._no_load()
            else:
                required_power, required_current, phases = self._no_load()
                log.message_debug_log("warning", "Keine PV-Leistung übrig.")
            self._process_data(chargepoint, required_power, required_current, phases)
        except Exception as e:
            log.exception_logging(e)

# Helperfunctions

    def _get_phases(self, chargepoint):
        """ ermittelt die maximal mögliche Anzahl Phasen, die von Konfiguration, Auto und Ladepunkt unterstützt wird.

        Parameter
        ---------
        chargepoint: dict
            Daten des Ladepunkts
        Return
        ------
        phases: int
            Anzahl Phasen
        """
        try:
            charging_ev = chargepoint.data["set"]["charging_ev"]
            config = chargepoint.data["config"]
            if charging_ev.ev_template.data["max_phases"] <= config["connected_phases"]:
                phases = charging_ev.ev_template.data["max_phases"]
            else:
                phases = config["connected_phases"]
            chargemode = charging_ev.data["control_parameter"]["chargemode"]
            chargemode_phases = data.general_data["general"].get_phases_chargemode(chargemode)
            if phases <= chargemode_phases:
                return phases
            else:
                return chargemode_phases
        except Exception as e:
            log.exception_logging(e)

    def _no_load(self):
        """ setzt die Parameter zum Stoppen der PV-Ladung

        Return
        ------
        required_power: float
            Leistung, mit der geladen werden soll
        required_current: float
            Stromstärke, mit der geladen werden soll
        phases: int
            Phasen, mit denen geladen werden soll
        """
        required_power = 0
        required_current = 0
        phases = 0
        return required_power, required_current, phases

    def _process_data(self, chargepoint, required_power, required_current, phases):
        """ setzt die ermittelte Anzahl Phasen, Stromstärke und Leistung in den Dictionarys, 
        publsihed sie und schreibt sie ins Log.

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
        """
        try:
            chargepoint.data["set"]["current"] = required_current
            chargepoint.data["set"]["phases_to_use"] = phases
            pub.pub("openWB/chargepoint/"+str(chargepoint.cp_num)+"/set/current", required_current)
            pub.pub("openWB/chargepoint/"+str(chargepoint.cp_num)+"/set/phases_to_use", phases)
            charging_ev = chargepoint.data["set"]["charging_ev"]
            log.message_debug_log("debug", "Algorithmus-Durchlauf für LP"+str(chargepoint.cp_num)+" beendet. Lademodus: "+charging_ev.charge_template.data["chargemode"]["selected"]+", Submodus: "+charging_ev.data["control_parameter"]["chargemode"]+", Prioritaet: "+str(charging_ev.charge_template.data["prio"]))
            log.message_debug_log("info", "LP: "+str(chargepoint.cp_num)+", Ladestrom: "+str(required_current)+"A, Phasen: "+str(phases)+", Ladeleistung: "+str(required_power)+"W")
            log.message_debug_log("debug", str(data.counter_data["evu"].data["set"]["consumption_left"])+"W EVU-Bezugs-Leistung, die fuer die folgenden Durchlaufe uebrig ist.")
            data.pv_data["pv"].put_stats()
            if required_current != 0:
                chargepoint.data["get"]["charge_state"] == True
            else:
                chargepoint.data["get"]["charge_state"] == False
            pub.pub("openWB/chargepoint/"+str(chargepoint.cp_num)+"/get/charge_state", chargepoint.data["get"]["charge_state"])
        except Exception as e:
            log.exception_logging(e)

    def _start_charging(self):
        try:
            data.pv_data["pv"].put_stats()
            data.counter_data["evu"].put_stats()
            log.message_debug_log("info", "Regelungszyklus beendet.")
            for cp in data.cp_data:
                chargepoint = data.cp_data[cp]
                if "set" in chargepoint.data:
                    if "charging_ev" in chargepoint.data["set"]:
                        # CP-Unterbrechung durchführen?
                        # Phasenumschaltung erforderlich?
                        pub.pub("openWB/chargepoint/"+str(chargepoint.cp_num)+"/get/power_all", (chargepoint.data["set"]["phases_to_use"]*chargepoint.data["set"]["current"]*230))
        except Exception as e:
            log.exception_logging(e)

# in Vorbereitung


    def distribute_unsued_evu_overhang(self):
        try:
            num_of_phases = 0
            for chargepoint in data.cp_data:
                if "set" in data.cp_data[chargepoint].data:
                    if "charging_ev" in data.cp_data[chargepoint].data["set"]:
                        if (data.cp_data[chargepoint].data["set"]["charging_ev"].charge_template.data["chargemode"]["selected"] == "pv_load" or data.cp_data[chargepoint].data["set"]["charging_ev"].data["control_parameter"]["chargemode"] == "pv_load") and data.cp_data[chargepoint].data["get"]["charge_state"]:
                            num_of_phases += data.cp_data[chargepoint].data["set"]["phases_to_use"]
            # mit oder ohne Einspeisungsgrenze??
            additional_current_per_phase = data.pv_data["pv"].power_for_pv_load(True) / 230 / num_of_phases
            phases = data.cp_data[chargepoint].data["set"]["phases_to_use"]
            for cp in data.cp_data:
                if "set" in data.cp_data[cp].data:
                    if "charging_ev" in data.cp_data[cp].data["set"]:
                        if (data.cp_data[chargepoint].data["set"]["charging_ev"].charge_template.data["chargemode"]["selected"] == "pv_load" or data.cp_data[chargepoint].data["set"]["charging_ev"].data["control_parameter"]["chargemode"] == "pv_load")  and data.cp_data[chargepoint].data["get"]["charge_state"]:
                            chargepoint = data.cp_data[cp]
                            # prüfen, ob Umschaltcountdown gestartet werden kann
                            current = chargepoint.data["set"]["charging_ev"].phase_switch_start_timer(chargepoint, additional_current_per_phase)
                            chargepoint.data["set"]["current"] = current
                            data.pv_data["pv"].allocate_pv_power(phases * 230 * current)
                            pub.pub("openWB/chargepoint/"+str(chargepoint.cp_num)+"/set/current", current)
                            log.message_debug_log("info", "Überschussladen an LP: "+str(chargepoint.cp_num)+", Ladestrom: "+str(current)+"A, Phasen: "+str(phases)+", Ladeleistung: "+str(phases * 230 * current)+"W")
            data.pv_data["pv"].put_stats()
        except Exception as e:
            log.exception_logging(e)
