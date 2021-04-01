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
        """
        log.message_debug_log("debug", "# Algorithmus-Start")
        # Lademodi in absteigender Priorität; Tupelinhalt: (eingestellter Modus, tatsächlich genutzter Modus, Priorität)
        chargemodes = ( ("scheduled_charging", "instant_charging", True), 
                        ("scheduled_charging", "instant_charging", False), 
                        (None, "time_charging", True), 
                        (None, "time_charging", False), 
                        ("instant_charging", "instant_charging", True), 
                        ("instant_charging", "instant_charging", False), 
                        ("pv_charging", "instant_charging", True), 
                        ("pv_charging", "instant_charging", False), 
                        ("scheduled_charging", "pv_charging", True),
                        ("scheduled_charging", "pv_charging", False), 
                        ("pv_charging", "pv_charging", True), 
                        ("pv_charging", "pv_charging", False), 
                        (None, "standby", True), 
                        (None, "standby", False), 
                        (None, "stop", True),
                        (None, "stop", False) )
                        
        # erstmal die PV-Überschuss-Ladung zurück nehmen, wenn kein Überschuss vorhanden ist
        log.message_debug_log("debug", "## Ueberschuss-Ladung ueber Mindeststrom bei PV-Laden zuruecknehmen.")
        self._reduce_used_evu_overhang()
       
        if data.counter_data["counter0"].data["set"]["loadmanagement"] == True:
            log.message_debug_log("debug", "## Ladung wegen aktiven Lastmanagements stoppen.")
            # Wenn trotz Rücknahme des PV-Überschussladens immer noch das Lastmanagement aktiv ist, LP abschalten. Dazu das Lademodi-Tupel rückwärts durchgehen und LP mit niedrig priorisiertem Lademodus zuerst stoppen.
            #Ist jetzt schon die Sicherung geflogen?
            for mode in reversed(chargemodes[:-4]):
                cp_to_stop = True
                while cp_to_stop == True:
                    cp_to_stop = self._switch_off_lowest_cp(mode)
                    if data.counter_data["counter0"].data["set"]["loadmanagement"] == False:
                        break
                if data.counter_data["counter0"].data["set"]["loadmanagement"] == False:
                        break
        else:
            log.message_debug_log("debug", "## Ladung muss nicht wegen aktiven Lastmanagements gestoppt werden.")

        if data.counter_data["counter0"].data["set"]["loadmanagement"] == True:
            log.message_debug_log("warning", "Bezug immer noch hoeher als maximaler Bezug, obwohl das Laden gestoppt wurde.")

         #Abschaltschwelle prüfen und ggf. Abschaltverzögerung starten
        for mode in reversed(chargemodes[10:-4]):
            if self._switch_off_threshold(mode) == False:
                break

        # Phasenumschaltung
        self._check_auto_phase_switch()

        # Überschuss für Ladepunkte verwenden, die noch nicht laden bzw. LP mit niedrigerer Ladepriorität abschalten, um LP mit höherer Priorität zu laden.
        while True:
            current_mode = None
            log.message_debug_log("debug", "## Zuteilung des Ueberschusses")
            for mode in chargemodes:
                if self._distribute_overhang(mode) == True:
                    # Lastmanagement verhindert Ladung
                    current_mode = chargemodes.index(mode)
                    break
            else:
                # kein Ladepunkt, der noch auf Zuteilung wartet
                log.message_debug_log("debug", "## Zuteilung beendet, da kein Ladepunkt mehr auf Zuteilung wartet.")
                break
            log.message_debug_log("debug", "## Zuteilung gestoppt, da erst die Ladung an einem Ladepunkt mit niedrigerer Prioritaet gestoppt werden muss.")
            # LP mit niedrigerer Priorität stoppen
            for mode in reversed(chargemodes[(current_mode+1):-4]):
                if self._switch_off_lowest_cp(mode) == True:
                    break
            # kein Ladepunkt vorhanden, dessen Ladung gestoppt werden kann
            else:
                # keine weitere Zuteilung
                log.message_debug_log("debug", "## Zuteilung beendet, da Lastmanagement aktiv und es kann kein LP mehr gestoppt werden.")
                break

        # Übrigen Überschuss auf Ladepunkte im PV-Modus verteilen
        log.message_debug_log("debug", "## Uebrigen Ueberschuss verteilen.")
        self._distribute_unused_evu_overhang()

        # LP stoppen, bei denen die Abschaltverzögerung abgelaufen ist (die frei werdende Leistung soll erst im nächsten Zyklus verteilt werden)
        for cp in data.cp_data:
            if "cp" in cp:
                chargepoint = data.cp_data[cp]
                if "charging_ev" in chargepoint.data["set"]:
                    if chargepoint.data["set"]["charging_ev"].data["control_parameter"]["chargemode"] == "pv_charging" and chargepoint.hw_data["get"]["charge_state"] == True:
                        if data.pv_data["all"].switch_off_check_timer(chargepoint) == True:
                            # Ladung stoppen
                            required_current, phases = self._no_load()
                            self._process_data(chargepoint, required_current, phases)
                            # in diesem Durchgang soll kein Strom zugeteilt werden
                            chargepoint.data["set"]["charging_ev"].data["control_parameter"]["chargemode"] = "stop"

    def _distribute_overhang(self, mode_tuple):
        """ verteilt den EVU-Überschuss und den maximalen Bezug auf die Ladepunkte, die dem Modus im Tupel entsprechen. 
        Die Funktion endet, wenn das Lastmanagement eingereift oder keine Ladepunkte mehr in diesem Modus vorhanden sind. 
        Die Zuteilung erfolgt gemäß der Reihenfolge in _get_preferenced_chargepoint.

        Parameter
        ---------
        mode_tuple: tuple
            enthält den eingestellten Lademodus, den tatsächlichen Lademodus und die Priorität

        Returns
        -------
        True: Lastmanagement hat eine Zuteilung verhindert.
        False: Es gibt keine LP, der auf Zuteilung wartet.
        """
        mode=mode_tuple[0]
        submode = mode_tuple[1]
        prio = mode_tuple[2]
        try:
            # LP, der abgeschaltet werden soll
            preferenced_chargepoints = []
            # enthält alle LP, auf die das Tupel zutrifft
            valid_chargepoints = {}
            for cp in data.cp_data:
                if "cp" in cp:
                    chargepoint = data.cp_data[cp]
                    if "charging_ev" in chargepoint.data["set"]:
                        charging_ev = chargepoint.data["set"]["charging_ev"]
                        #set-> current enthält einen Wert, wenn das EV in diesem Zyklus eingeschaltet werden soll, aktuell aber noch nicht lädt.
                        if "current" in chargepoint.data["set"]:
                            if chargepoint.data["set"]["current"] != 0:
                                continue
                        if mode == None:
                            if(charging_ev.charge_template.data["prio"] == prio) and (charging_ev.data["control_parameter"]["chargemode"] == submode):
                                valid_chargepoints[chargepoint] = None
                        elif (charging_ev.charge_template.data["prio"] == prio) and (charging_ev.charge_template.data["chargemode"]["selected"] == mode) and (charging_ev.data["control_parameter"]["chargemode"] == submode):
                            valid_chargepoints[chargepoint] = None
            preferenced_chargepoints = self._get_preferenced_chargepoint(valid_chargepoints, True)

            if len(preferenced_chargepoints) == 0:
                # Es gibt keine Ladepunkte in diesem Lademodus, die noch nicht laden.
                return False
            else:
                for cp in preferenced_chargepoints:
                    self._distribute_power_to_cp(cp)
                    if data.counter_data["counter0"].data["set"]["loadmanagement"] == False:
                        log.message_debug_log("info", "LP: "+str(cp.cp_num)+", Ladestrom: "+str(cp.data["set"]["current"])+"A, Phasen: "+str(cp.data["set"]["phases_to_use"])+", Ladeleistung: "+str((cp.data["set"]["phases_to_use"]*cp.data["set"]["current"]*230))+"W")
                    else:
                        #Lastmanagement hat eingegriffen und die Zuteilung verhindert
                        return True
        except Exception as e:
            log.exception_logging(e)

    def _switch_off_lowest_cp(self, mode_tuple):
        """ schaltet einen Ladepunkt gemäß dem Modus im Tupel ab. Gibt es mehrere Ladepunkte, auf die das Tupel zutrifft, wird die Reihenfolge durch _get_preferenced_chargepoint festgelegt.

        Parameter
        ---------
        mode_tuple: tuple
            enthält den eingestellten Lademodus, den tatsächlichen Lademodus und die Priorität

        Return
        ------
        True: Es wurde ein Ladepunkt abgeschaltet.
        False: Es gibt keine Ladepunkte in diesem Lademodus, die noch nicht laden oder die noch gestoppt werden können.
        """
        mode=mode_tuple[0]
        submode = mode_tuple[1]
        prio = mode_tuple[2]
        try:
            # LP, der abgeschaltet werden soll
            preferenced_chargepoints = []
            # enthält alle LP, auf die das Tupel zutrifft
            valid_chargepoints = {}
            for cp in data.cp_data:
                if "cp" in cp:
                    chargepoint = data.cp_data[cp]
                    #set-> current enthält einen Wert, wenn das EV in diesem Zyklus eingeschaltet werden soll, aktuell aber noch nicht lädt.
                    if "current" in chargepoint.data["set"]:
                        if chargepoint.data["set"]["current"] == 0:
                            continue
                    if "charging_ev" in chargepoint.data["set"]:
                        charging_ev = chargepoint.data["set"]["charging_ev"]
                        if mode == None:
                            if(charging_ev.charge_template.data["prio"] == prio) and (charging_ev.data["control_parameter"]["chargemode"] == submode):
                                valid_chargepoints[chargepoint] = None
                        elif (charging_ev.charge_template.data["prio"] == prio) and (charging_ev.charge_template.data["chargemode"]["selected"] == mode) and (charging_ev.data["control_parameter"]["chargemode"] == submode):
                            valid_chargepoints[chargepoint] = None
            preferenced_chargepoints = self._get_preferenced_chargepoint(valid_chargepoints, False)

            if len(preferenced_chargepoints) == 0:
                # Es gibt keine Ladepunkte in diesem Lademodus, die noch nicht laden oder die noch gestoppt werden können.
                return False
            else:
                required_current, phases= self._no_load()
                self._process_data(preferenced_chargepoints[0], required_current, phases)
                log.message_debug_log("debug", "Ladung an LP"+str(preferenced_chargepoints[0].cp_num)+" gestoppt.")
                loadmanagement.loadmanagement((preferenced_chargepoints[0].hw_data["get"]["power_all"]*-1), 0, 0)
                return True
        except Exception as e:
            log.exception_logging(e)

    def _switch_off_threshold(self, mode_tuple):
        """Gibt es mehrere Ladepunkte, auf die das Tupel zutrifft, wird die Reihenfolge durch _get_preferenced_chargepoint festgelegt.
        Dann wird geprüft, ob die Abschaltschwelle erreicht wurde.

        Parameter
        ---------
        mode_tuple: tuple
            enthält den eingestellten Lademodus, den tatsächlichen Lademodus und die Priorität

        Return
        ------
        True: Es wurde ein Ladepunkt abgeschaltet.
        False: Es gibt keine Ladepunkte in diesem Lademodus, die noch nicht laden oder die noch gestoppt werden können.
        """
        mode=mode_tuple[0]
        submode = mode_tuple[1]
        prio = mode_tuple[2]
        try:
            # LP, der abgeschaltet werden soll
            preferenced_chargepoints = []
            # enthält alle LP, auf die das Tupel zutrifft
            valid_chargepoints = {}
            for cp in data.cp_data:
                if "cp" in cp:
                    chargepoint = data.cp_data[cp]
                    #chargestate, weil nur die geprüft werden sollen, die tatsächlich laden und nicht die, die in diesem Zyklus eingeschaltet wurden.
                    if chargepoint.hw_data["get"]["charge_state"] == False:
                        continue
                    if "charging_ev" in chargepoint.data["set"]:
                        charging_ev = chargepoint.data["set"]["charging_ev"]
                        if mode == None:
                            if(charging_ev.charge_template.data["prio"] == prio) and (charging_ev.data["control_parameter"]["chargemode"] == submode):
                                valid_chargepoints[chargepoint] = None
                        elif (charging_ev.charge_template.data["prio"] == prio) and (charging_ev.charge_template.data["chargemode"]["selected"] == mode) and (charging_ev.data["control_parameter"]["chargemode"] == submode):
                            valid_chargepoints[chargepoint] = None
            preferenced_chargepoints = self._get_preferenced_chargepoint(valid_chargepoints, False)

            if len(preferenced_chargepoints) == 0:
                # Es gibt keine Ladepunkte in diesem Lademodus, die noch nicht laden oder die noch gestoppt werden können.
                return True
            else:
                # Solange die Liste durchgehen, bis die Abschaltschwelle nicht mehr erreicht wird.
                for cp in preferenced_chargepoints:
                    if cp.data["set"]["current"] != 0:
                        data.pv_data["all"].switch_off_check_threshold(cp, self._get_bat_and_evu_overhang())
        except Exception as e:
            log.exception_logging(e)
    
    def _get_preferenced_chargepoint(self, valid_chargepoints, start):
        """ermittelt aus dem Dictionary den Ladepunkt, der eindeutig die Bedingung erfüllt. Die Bedingungen sind:
        geringste Mindeststromstärke, niedrigster SoC, frühester Ansteck-Zeitpunkt(Einschalten)/Lademenge(Abschalten), niedrigste Ladepunktnummer.
        Parameter
        ---------
        valid_chargepoints: dict
            enthält alle Ladepunkte gleicher Priorität und Lademodus, die noch nicht laden und keine Zuteilung haben.
        start: bool
            Soll die Ladung gestoppt oder gestartet werden?

        Return
        ------
        preferenced_chargepoints: list
            Liste der Ladepunkte in der Reihenfolge, in der sie geladen/gestoppt werden sollen.
        """
        try:
            preferenced_chargepoints = []
            # Bedingungen in der Reihenfolge, in der sie geprüft werden. 3. Bedingung, ist abhängig davon, ob ein- oder ausgeschaltet werden soll.
            if start == True:
                condition_types = ("min_current", "soc", "plug_in", "cp_num") 
            else:
                condition_types = ("min_current", "soc", "charged_since_plugged", "cp_num") 
            # Bedingung, die geprüft wird (entspricht Index von condition_types)
            condition = 0
            if len(valid_chargepoints) > 0:
                while len(valid_chargepoints) > 0:
                    # entsprechend der Bedingung die Values im Dictionary füllen
                    if condition_types[condition] == "min_current":
                        valid_chargepoints.update((cp, cp.data["set"]["charging_ev"].data["control_parameter"]["required_current"]) for cp, val in valid_chargepoints.items())
                    elif condition_types[condition] == "soc":
                        valid_chargepoints.update((cp, cp.data["set"]["charging_ev"].data["get"]["soc"]) for cp, val in valid_chargepoints.items())
                    elif condition_types[condition] == "plug_in":
                        valid_chargepoints.update((cp, cp.data["get"]["plug_time"]) for cp, val in valid_chargepoints.items())
                    elif condition_types[condition] == "charged_since_plugged":
                        valid_chargepoints.update((cp, cp.data["get"]["charged_since_plugged_counter"]) for cp, val in valid_chargepoints.items())
                    else:
                        valid_chargepoints.update((cp, cp.cp_num) for cp, val in valid_chargepoints.items())

                    # kleinsten Value im Dictionary ermitteln
                    min_value = min(valid_chargepoints.values())
                    # dazugehörige Keys ermitteln
                    min_cp = [key for key in valid_chargepoints if valid_chargepoints[key] == min_value]
                    if len(min_cp) > 1:
                        # Wenn es mehrere LP gibt, die den gleichen Minimalwert haben, nächste Bedingung prüfen.
                        condition += 1
                    else:
                        preferenced_chargepoints.append(min_cp[0])
                        valid_chargepoints.pop(min_cp[0])

            return preferenced_chargepoints
        except Exception as e:
            log.exception_logging(e)

    def _distribute_power_to_cp(self, chargepoint):
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
            if charging_ev.data["control_parameter"]["chargemode"] == "pv_charging":
                self._calc_pv_charging(chargepoint, required_power,
                                required_current, phases)
            elif (charging_ev.data["control_parameter"]["chargemode"] == "stop" or (charging_ev.data["control_parameter"]["chargemode"] == "standby")):
                required_current, phases = self._no_load()
                self._process_data(chargepoint, required_current, phases)
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
        """
        try:
            # PV-Strom nutzen
            overhang_power_left = data.pv_data["all"].overhang_left_with_without_feed_in_limit(False)
            if overhang_power_left > 0:
                overhang_power_left -= required_power
                if overhang_power_left > 0:
                    if data.pv_data["all"].allocate_pv_power(required_power) == False:
                        required_current = 0
                        phases = 0
                    self._process_data(chargepoint, required_current, phases)
                else:
                    evu_power = overhang_power_left *-1 # muss bezogen werden
                    pv_power = required_power - evu_power
                    evu_current = required_power / (phases * 230)
                    if loadmanagement.loadmanagement(evu_power, evu_current, phases) == False:
                        if data.pv_data["all"].allocate_pv_power(pv_power) == False:
                            required_current = 0
                            phases = 0
                    else:
                        required_current, phases= self._no_load()
                    self._process_data(chargepoint, required_current, phases)
                return
            # Bezug
            if loadmanagement.loadmanagement(required_power, required_current, phases) == True:
                required_current, phases= self._no_load()
            self._process_data(chargepoint, required_current, phases)
        except Exception as e:
            log.exception_logging(e)

    def _calc_pv_charging(self, chargepoint, required_power, required_current, phases):
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
        """
        try:
            if chargepoint.data["set"]["charging_ev"].charge_template.data["chargemode"]["selected"] == "scheduled_charging" and "pv_charging" not in chargepoint.data["set"]["charging_ev"].charge_template.data["chargemode"]:
                required_current, phases = self._no_load()
                log.message_debug_log("warning", "PV-Laden im Modus Zielladen aktiv und es wurden keine Einstellungen für PV-Laden konfiguriert.")
            else:
                if self._check_cp_without_feed_in_is_prioritised(chargepoint) == True:
                    required_current, phases = data.pv_data["all"].switch_on(chargepoint, required_power, required_current, phases, data.bat_module_data["all"].power_for_bat_charging())
            self._process_data(chargepoint, required_current, phases)
        except Exception as e:
            log.exception_logging(e)

    def _check_cp_without_feed_in_is_prioritised(self, chargepoint):
        """ Wenn ein LP im Sbumodus PV-Laden nicht die Maximalstromstärke zugeteilt bekommen hat, 
        darf ein LP mit Einspeiungsgrenze nicht eingeschaltet werden.

        Parameter
        ---------
        chargepoint: dict
            Daten des Ladepunkts

        Return
        ------
        True: LP darf geladen werden.
        False: LP mit Einspeisungsgrenze darf nicht geladen werden.
        """
        try:
            if chargepoint.data["set"]["charging_ev"].charge_template.data["chargemode"]["pv_charging"]["feed_in_limit"] == True:
                for cp in data.cp_data:
                    if "set" in data.cp_data[cp].data:
                        charging_ev = data.cp_data[cp].data["set"]["charging_ev"]
                        if charging_ev.data["control_parameter"]["chargemode"] == "pv_charging" and charging_ev.charge_template.data["chargemode"]["pv_charging"]["feed_in_limit"] == False:
                            if data.cp_data[cp].data["set"]["current"] != charging_ev.ev_template.data["max_current"]:
                                return False
            return True
        except Exception as e:
            log.exception_logging(e)

    def _distribute_unused_evu_overhang(self):
        """ prüft, ob für LP ohne Einspeisungsgrenze noch EVU-Überschuss übrig ist und dann für die LP mit Einspeiungsgrenze.
        """
        try:
            if data.pv_data["all"].overhang_left_with_without_feed_in_limit(False) != 0:
                if data.pv_data["all"].overhang_left_with_without_feed_in_limit(False) > 0:
                    self._distribution(False, False)
                    self._distribution(False, True)
                if data.pv_data["all"].overhang_left_with_without_feed_in_limit(True) > 0:
                    self._distribution(True, True)
                    self._distribution(True, False)
            data.pv_data["all"].put_stats()
        except Exception as e:
            log.exception_logging(e)

    def _reduce_used_evu_overhang(self):
        """ prüft, ob für LP ohne Einspeisungsgrenze noch EVU-Überschuss zurückgenommen werden muss und dann für die LP mit Einspeiungsgrenze.
        """
        try:
            if data.pv_data["all"].overhang_left_with_without_feed_in_limit(False) != 0:
                if data.pv_data["all"].overhang_left_with_without_feed_in_limit(True) < 0:
                    self._distribution(True, False)
                    self._distribution(True, True)
                if data.pv_data["all"].overhang_left_with_without_feed_in_limit(False) < 0:
                    self._distribution(False, True)
                    self._distribution(False, False)
            data.pv_data["all"].put_stats()
        except Exception as e:
            log.exception_logging(e)

    def _distribution(self, feed_in_limit, bat_prio):
        """ Verteilt den verbleibenden EVU-Überschuss gleichmäßig auf alle genutzten Phasen. Dazu wird zunächst die Anzahl der Phasen ermittelt, auf denen geladen wird.
        Danach wird der Überschuss pro Phase ermittelt und auf die Phasen aufgeschlagen.

        Parameter
        ---------
        feed_in_limit: bool
            Einspeisungsgrenze aktiv/inaktiv 
        """
        try:
            num_of_phases = 0
            # Anzahl aller genutzten Phasen ermitteln
            for chargepoint in data.cp_data:
                if "set" in data.cp_data[chargepoint].data:
                    if "charging_ev" in data.cp_data[chargepoint].data["set"]:
                        charging_ev = data.cp_data[chargepoint].data["set"]["charging_ev"]
                        if charging_ev.data["control_parameter"]["chargemode"] == "pv_charging":
                            if (data.cp_data[chargepoint].data["set"]["current"] != 0 and 
                                    charging_ev.charge_template.data["chargemode"]["pv_charging"]["feed_in_limit"] == feed_in_limit and 
                                    charging_ev.charge_template.data["chargemode"]["pv_charging"]["bat_prio"] == bat_prio):
                                num_of_phases += data.cp_data[chargepoint].data["set"]["phases_to_use"]
            # Ladung aktiv?
            if num_of_phases > 0:
                # Wenn das EV Vorrang hat, kann die Ladeleistung des Speichers zum Laden des EV verwendet werden.
                if bat_prio == False:
                    bat_overhang = data.bat_module_data["all"].data["set"]["charging_power_left"]
                else:
                    bat_overhang = 0
                # pos. Wert -> Ladestrom wird erhöht, negativer Wert -> Ladestrom wird reduziert
                current_diff_per_phase = (data.pv_data["all"].overhang_left_with_without_feed_in_limit(feed_in_limit) + bat_overhang) / 230 / num_of_phases
                for cp in data.cp_data:
                    if "set" in data.cp_data[cp].data:
                        chargepoint = data.cp_data[cp]
                        if "charging_ev" in data.cp_data[cp].data["set"]:
                            charging_ev = chargepoint.data["set"]["charging_ev"]
                            if charging_ev.charge_template.data["chargemode"]["selected"] == "pv_charging" or charging_ev.data["control_parameter"]["chargemode"] == "pv_charging":
                                if (chargepoint.data["set"]["current"] != 0 and 
                                        charging_ev.charge_template.data["chargemode"]["pv_charging"]["feed_in_limit"] == feed_in_limit and 
                                        charging_ev.charge_template.data["chargemode"]["pv_charging"]["bat_prio"] == bat_prio):
                                    phases = chargepoint.data["set"]["phases_to_use"]
                                    # Einhalten des Mindeststroms des Lademodus und Maximalstroms des EV
                                    current = charging_ev.check_min_max_current_for_pv_charging(current_diff_per_phase+chargepoint.data["set"]["current"])
                                    chargepoint.data["set"]["current"] = current
                                    power_diff = phases * 230 * (current - chargepoint.data["set"]["current"])

                                    # Laden nur mit der Leistung, die vorher der Speicher bezogen hat
                                    if ( bat_overhang - power_diff) > 0:
                                        if data.bat_module_data["all"].allocate_bat_power(power_diff) == False:
                                            current = 0
                                    # Laden mit EVU-Überschuss und der Leistung, die vorher der Speicher bezogen hat
                                    elif bat_overhang > 0:
                                        pv_power = power_diff - bat_overhang
                                        if data.pv_data["all"].allocate_pv_power(pv_power) == False:
                                            current = 0
                                        elif data.bat_module_data["all"].allocate_bat_power(bat_overhang) == False:
                                            current = 0
                                    # Laden nur mit EVU-Überschuss bzw. Reduktion des EVU-Bezugs
                                    else:
                                        if data.pv_data["all"].allocate_pv_power(power_diff) == False:
                                            current = 0

                                    pub.pub("openWB/chargepoint/"+str(chargepoint.cp_num)+"/set/current", current)
                                    log.message_debug_log("info", "Überschussladen an LP: "+str(chargepoint.cp_num)+", Ladestrom: "+str(current)+"A, Phasen: "+str(phases)+", Ladeleistung: "+str(phases * 230 * current)+"W")
        except Exception as e:
            log.exception_logging(e)

    def _check_auto_phase_switch(self):
        """ geht alle LP durch und prüft, ob eine Ladung aktiv ist, ob automatische Phasenumschaltung 
        möglich ist und ob ob ein Timer gestartet oder gestoppt werden muss oder ob ein Timer abgelaufen ist.
        """
        try:
            for cp in data.cp_data:
                if "set" in data.cp_data[cp].data:
                    chargepoint = data.cp_data[cp]
                    if "charging_ev" in data.cp_data[cp].data["set"]:
                        if chargepoint.data["config"]["auto_phase_switch_hw"] == True and chargepoint.hw_data["get"]["charge_state"] == True:
                            chargepoint.data["set"]["phases_to_use"] = chargepoint.data["set"]["charging_ev"].auto_phase_switch(chargepoint.hw_data["get"]["phases_in_use"], chargepoint.hw_data["get"]["current"])
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
            if chargemode_phases == "auto":
                if phases <= chargepoint.data["set"]["phases_to_use"]:
                    return chargepoint.data["set"]["phases_to_use"]
                else:
                    phases
            elif phases <= chargemode_phases:
                return phases
            else:
                return chargemode_phases
        except Exception as e:
            log.exception_logging(e)

    def _no_load(self):
        """ setzt die Parameter zum Stoppen der PV-Ladung

        Return
        ------
        required_current: float
            Stromstärke, mit der geladen werden soll
        phases: int
            Phasen, mit denen geladen werden soll
        """
        required_current = 0
        phases = 0
        return required_current, phases

    def _process_data(self, chargepoint, required_current, phases):
        """ setzt die ermittelte Anzahl Phasen, Stromstärke und Leistung in den Dictionarys, 
        publsihed sie und schreibt sie ins Log.

        Parameter
        ---------
        chargepoint: dict
            Daten des Ladepunkts
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
            data.pv_data["all"].put_stats()
        except Exception as e:
            log.exception_logging(e)

    def _get_bat_and_evu_overhang(self):
        """
        """
        return data.bat_module_data["all"].data["get"]["power"] + data.pv_data["all"].data["set"]["available_power"]