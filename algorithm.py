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
       
       
        loadmanagement_state, overloaded_counters = loadmanagement.loadmanagement_for_counters()
        if loadmanagement_state == True:
            log.message_debug_log("debug", "## Ladung wegen aktiven Lastmanagements stoppen.")
            # Zähler mit der größten Überlastung ermitteln
            overloaded_counters = sorted(overloaded_counters.items(), key=lambda e: e[1][1], reverse = True)
            n = 0 # Zähler, der betrachtet werden soll
            # set current auf den maximalen get current stellen, damit der tatsächlich genutzte Strom reduziert wird und nicht der maximal nutzbare, 
            # der ja evtl gar nicht voll ausgenutzt wird, sodass die Reduzierung wirkungslos wäre. Außerdem bleibt get current während des Zyklus unverändert,
            # während set current in den verschiedenen Phasen immer wieder angepasst werden kann.
            for cp in data.cp_data:
                if "cp" in cp:
                    data.cp_data[cp].data["set"]["current"] = max(data.cp_data[cp].data["get"]["current"])
            while True:
                chargepoints = loadmanagement.perform_loadmanagement(overloaded_counters[n][0])
                overshoot = overloaded_counters[n][1][0]
                # Das Lademodi-Tupel rückwärts durchgehen und LP mit niedrig priorisiertem Lademodus zuerst reduzieren/stoppen.
                for mode in reversed(chargemodes[:-4]):
                    overshoot = self._down_regulation(mode, chargepoints, overshoot, overloaded_counters[n][1][1])
                    if overshoot == 0:
                        break
                if overshoot == 0:
                    # Nach dem Aktualisieren der Werte sollte der Zähler verschwunden sein, weil man genügend LP abschalten konnte
                    n=0
                else:
                    # Wenn die Überlastung nicht komplett beseitigt werden konnte, Zahlen aktualisieren und mit nächstem Zähler weitermachen.
                    n += 1
                if n > len(overloaded_counters)-1:
                    # keine Zähler mehr, an denen noch reduziert werden kann. Wieder beim ersten Zähler anfangen, diesemal werden die 
                    # LP dann abgeschaltet.
                    n = 0
                # Werte aktualisieren
                loadmanagement_state, overloaded_counters = loadmanagement.loadmanagement_for_counters()
                if loadmanagement_state == False:
                    # Lastmanagemnt ist nicht mehr aktiv
                    break
                overloaded_counters = sorted(overloaded_counters.items(), key=lambda e: e[1][1], reverse = True)
        else:
            log.message_debug_log("debug", "## Ladung muss nicht wegen aktiven Lastmanagements gestoppt werden.")
            # Ladepunkte, die nicht mit Maximalstromstärke laden, können wieder hochgeregelt werden.
            for mode in chargemodes[:-4]:
                self._adjust_chargepoints(mode)

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
                state, chargepoint, overloaded_counters = self._distribute_overhang(mode)
                if state == True:
                    # Lastmanagement verhindert Ladung
                    current_mode = chargemodes.index(mode)
                    break
            else:
                # kein Ladepunkt, der noch auf Zuteilung wartet
                log.message_debug_log("debug", "## Zuteilung beendet, da kein Ladepunkt mehr auf Zuteilung wartet.")
                break
            # Zähler mit der größten Überlastung ermitteln
            overloaded_counters = sorted(overloaded_counters.items(), key=lambda e: e[1][1], reverse = True)
            # Ergebnisse des Lastmanagements holen, das beim Einschalten durchgeführt worden ist. Es ist ausreichend, 
            # Zähler mit der größten Überlastung im Pfad zu betrachten. Kann diese nicht eliminiert werden, kann der Ladpunkt nicht laden. 
            chargepoints = loadmanagement.perform_loadmanagement(overloaded_counters[0][0])
            remaining_current_overshoot = overloaded_counters[0][1][0]
            # LP mit niedrigerer Priorität reduzieren und ggf. stoppen
            for mode in reversed(chargemodes[(current_mode+1):-4]):
                remaining_current_overshoot = self._down_regulation(mode, chargepoints, remaining_current_overshoot, overloaded_counters[0][1][1], prevent_stop = False)
                if remaining_current_overshoot == 0:
                    break
            else:
                # Ladepunkt, der gestartet werden soll reduzieren
                remaining_current_overshoot = self._perform_down_regulation([chargepoint], remaining_current_overshoot, overloaded_counters[0][1][1], prevent_stop = True)
                # Ladepunkte mit gleicher Priorität reduzieren. Diese dürfen nicht gestoppt werden.
                if remaining_current_overshoot != 0:
                    remaining_current_overshoot = self._down_regulation(chargemodes[current_mode], chargepoints, remaining_current_overshoot, overloaded_counters[0][1][1], prevent_stop = True)
                if remaining_current_overshoot != 0:
                    # Ladepunkt darf nicht laden
                    remaining_current_overshoot = self._perform_down_regulation([chargepoint], remaining_current_overshoot, overloaded_counters[0][1][1], prevent_stop = False)
                    # keine weitere Zuteilung
                    log.message_debug_log("debug", "## Zuteilung beendet, da Lastmanagement aktiv und es kann kein LP mehr gestoppt werden.")
                    break
                # Ladepunkte, die reduziert wurden und trotzdem keine weitere Ladung gestartet werden konnte, können wieder hochgeregelt werden.
                for mode in chargemodes[:-4]:
                    self._adjust_chargepoints(mode)

        # Übrigen Überschuss auf Ladepunkte im PV-Modus verteilen
        log.message_debug_log("debug", "## Uebrigen Ueberschuss verteilen.")
        self._distribute_unused_evu_overhang()

        # LP stoppen, bei denen die Abschaltverzögerung abgelaufen ist (die frei werdende Leistung soll erst im nächsten Zyklus verteilt werden)
        for cp in data.cp_data:
            if "cp" in cp:
                chargepoint = data.cp_data[cp]
                if chargepoint.data["set"]["charging_ev"] != -1:
                    if chargepoint.data["set"]["charging_ev"].data["control_parameter"]["chargemode"] == "pv_charging" and chargepoint.data["get"]["charge_state"] == True:
                        if data.pv_data["all"].switch_off_check_timer(chargepoint) == True:
                            # Ladung stoppen
                            required_current, phases = no_load()
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
                    if chargepoint.data["set"]["charging_ev"] != -1:
                        charging_ev = chargepoint.data["set"]["charging_ev"]
                        #set-> current enthält einen Wert, wenn das EV in diesem Zyklus eingeschaltet werden soll, aktuell aber noch nicht lädt.
                        if "current" in chargepoint.data["set"]:
                            if chargepoint.data["set"]["current"] != 0:
                                continue
                        if( (charging_ev.charge_template.data["prio"] == prio) and 
                            (charging_ev.charge_template.data["chargemode"]["selected"] == mode or mode == None) and 
                            (charging_ev.data["control_parameter"]["chargemode"] == submode)):
                            valid_chargepoints[chargepoint] = None
            preferenced_chargepoints = self._get_preferenced_chargepoint(valid_chargepoints, True)

            if len(preferenced_chargepoints) == 0:
                # Es gibt keine Ladepunkte in diesem Lademodus, die noch nicht laden.
                return False, None, None
            else:
                for cp in preferenced_chargepoints:
                    overloaded_counters = self._distribute_power_to_cp(cp)
                    log.message_debug_log("info", "LP: "+str(cp.cp_num)+", Ladestrom: "+str(cp.data["set"]["current"])+"A, Phasen: "+str(cp.data["set"]["phases_to_use"])+", Ladeleistung: "+str((cp.data["set"]["phases_to_use"]*cp.data["set"]["current"]*230))+"W")
                    data.counter_data["counter0"].print_stats()
                    if data.counter_data["all"].data["set"]["loadmanagement"] == True:
                        #Lastmanagement hat eingegriffen und die Zuteilung verhindert
                        log.message_debug_log("debug", "Zuteilung gestoppt, da für die Ladung an LP"+str(cp.cp_num)+" erst ein Ladepunkt mit gleicher/niedrigerer Prioritaet reduziert/gestoppt werden muss.")
                        return True, cp, overloaded_counters
                else:
                    return False, None, None
        except Exception as e:
            log.exception_logging(e)

    def _down_regulation(self, mode_tuple, cps_to_reduce, max_current_overshoot, max_overshoot_phase, prevent_stop = False):
        """ schaltet einen Ladepunkt gemäß dem Modus im Tupel ab. Gibt es mehrere Ladepunkte, auf die das Tupel zutrifft, wird die Reihenfolge durch _get_preferenced_chargepoint festgelegt.

        Parameter
        ---------
        mode_tuple: tuple
            enthält den eingestellten Lademodus, den tatsächlichen Lademodus und die Priorität
        cps_to_reduce: list
            Liste der Ladepunkte, die berücksichtigt werden sollen
        max_current_overshoot: int
            maximale Überschreitung der Stromstärke, um diesen Wert soll die Ladung reduziert werden
        max_overshoot_phase: int
            Phase, in der die maximale Stromstärke erreicht wird (0, wenn alle Phasen berücksichtigt werden sollen.)
        prevent_stop: bool
            Ladung darf gestoppt werden. Wird diese Funktion nicht zur Durchführung des Lastmanagements genutzt, darf einem ladenden Ladepunkt nicht die Freigabe entzogen werden.

        Return
        ------
        True: Es wurde ein Ladepunkt abgeschaltet.
        False: Es gibt keine Ladepunkte in diesem Lademodus, die noch nicht laden oder die noch gestoppt werden können.
        remaining_current_overshoot: int
            Verbleibende Überlastung
        """
        mode=mode_tuple[0]
        submode = mode_tuple[1]
        prio = mode_tuple[2]
        try:
            # LP, der abgeschaltet werden soll
            preferenced_chargepoints = []
            # enthält alle LP, auf die das Tupel zutrifft
            valid_chargepoints = {}
            for cp in cps_to_reduce:
                # Die Funktion kann auch mit der Cp-Liste aus dem Data-Modul genutzt werden, deshalb die if-Abfrage.
                if "cp" in cp:
                    chargepoint = data.cp_data[cp]
                    if "current" in chargepoint.data["set"]:
                        if chargepoint.data["set"]["current"] == 0:
                            continue
                    if chargepoint.data["set"]["charging_ev"] != -1:
                        charging_ev = chargepoint.data["set"]["charging_ev"]
                        if((charging_ev.charge_template.data["prio"] == prio) and 
                                (charging_ev.charge_template.data["chargemode"]["selected"] == mode or mode == None) and 
                                (charging_ev.data["control_parameter"]["chargemode"] == submode) and
                                (chargepoint.data["get"]["phases_in_use"] >= max_overshoot_phase)):
                            valid_chargepoints[chargepoint] = None
            preferenced_chargepoints = self._get_preferenced_chargepoint(valid_chargepoints, False)
            
            return self._perform_down_regulation(preferenced_chargepoints, max_current_overshoot, max_overshoot_phase, prevent_stop)
        except Exception as e:
            log.exception_logging(e)

    def _perform_down_regulation(self, preferenced_chargepoints, max_current_overshoot, max_overshoot_phase, prevent_stop = False):
        try:
            if len(preferenced_chargepoints) == 0:
                # Es gibt keine Ladepunkte in diesem Lademodus, die noch nicht laden oder die noch gestoppt werden können.
                return max_current_overshoot
            else:
                for cp in preferenced_chargepoints:
                    # Wenn der LP erst in diesem Zyklus eingeschaltet wird, sind noch keine phases_in_use hinterlegt.
                    if cp.data["get"]["charge_state"] == False:
                        phases = cp.data["set"]["phases_to_use"]
                    else:
                        phases = cp.data["get"]["phases_in_use"]
                    # Wenn max_overshoot_phase 0 ist, wurde die maximale Gesamtleistung überschrittten und max_current_overshoot muss, 
                    # wenn weniger als 3 Phasen genutzt werden, entsprechend multipliziert werden.
                    if max_overshoot_phase == 0 and phases < 3:
                        remaining_current_overshoot = max_current_overshoot * (3 - phases +1)
                    else:
                        remaining_current_overshoot = max_current_overshoot
                    if cp.data["set"]["current"] != 0:
                        considered_current = cp.data["set"]["current"]
                    else:
                        # Dies ist der aktuell betrachtete Ladepunkt. Es wurde noch kein Strom gesetzt.
                        considered_current = cp.data["set"]["charging_ev"].data["control_parameter"]["required_current"]
                    adaptable_current = considered_current - cp.data["set"]["charging_ev"].ev_template.data["min_current"]
                    # Der Strom kann nicht weiter reduziert werden.
                    if adaptable_current <= 0:
                        # Ladung darf gestoppt werden.
                        if prevent_stop == False:
                            taken_current = cp.data["set"]["current"]*-1
                            remaining_current_overshoot -= taken_current
                            required_current = 0
                            self._process_data(cp, 0, 0)
                            log.message_debug_log("debug", "Ladung an LP"+str(cp.cp_num)+" gestoppt.")
                        else:
                            continue
                    else:
                        if adaptable_current < remaining_current_overshoot:
                            remaining_current_overshoot -= adaptable_current
                            taken_current = adaptable_current * -1
                        else:
                            taken_current = remaining_current_overshoot * -1
                            remaining_current_overshoot = 0
                        required_current = considered_current+taken_current
                        log.message_debug_log("debug", "Ladung an LP"+str(cp.cp_num)+" um "+str(taken_current)+"A angepasst.")
                    adapted_power = taken_current * 230 * phases
                    self._process_data(cp, required_current, phases)
                    # Werte aktualisieren
                    loadmanagement.loadmanagement_for_cp(cp, adapted_power, taken_current, phases)
                    data.counter_data["counter0"].print_stats()
                    # Wenn max_overshoot_phase 0 ist, wurde die maximale Gesamtleistung überschrittten und max_current_overshoot muss, 
                    # wenn weniger als 3 Phasen genutzt werden, entsprechend dividiert werden.
                    if max_overshoot_phase == 0 and phases < 3:
                        remaining_current_overshoot = remaining_current_overshoot / (3 - phases +1)
                    if remaining_current_overshoot < 0.01:
                        break
                    else:
                        max_current_overshoot = remaining_current_overshoot
                return remaining_current_overshoot
        except Exception as e:
            log.exception_logging(e)

    def _adjust_chargepoints(self, mode_tuple):
        """ schaltet einen Ladepunkt gemäß dem Modus im Tupel ab. Gibt es mehrere Ladepunkte, auf die das Tupel zutrifft, wird die Reihenfolge durch _get_preferenced_chargepoint festgelegt.

        Parameter
        ---------
        mode_tuple: tuple
            enthält den eingestellten Lademodus, den tatsächlichen Lademodus und die Priorität
        cps_to_reduce: list
            Liste der Ladepunkte, die berücksichtigt werden sollen
        max_current_overshoot: int
            maximale Überschreitung der Stromstärke, um diesen Wert soll die Ladung reduziert werden
        max_overshoot_phase: int
            Phase, in der die maximale Stromstärke erreicht wird (0, wenn alle Phasen berücksichtigt werden sollen.)
        prevent_stop: bool
            Ladung darf gestoppt werden. Wird diese Funktion nicht zur Durchführung des Lastmanagements genutzt, darf einem ladenden Ladepunkt nicht die Freigabe entzogen werden.

        Return
        ------
        True: Es wurde ein Ladepunkt abgeschaltet.
        False: Es gibt keine Ladepunkte in diesem Lademodus, die noch nicht laden oder die noch gestoppt werden können.
        remaining_current_overshoot: int
            Verbleibende Überlastung
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
                # Die Funktion kann auch mit der Cp-Liste aus dem Data-Modul genutzt werden, deshalb die if-Abfrage.
                if "cp" in cp:
                    chargepoint = data.cp_data[cp]
                    if "current" in chargepoint.data["set"]:
                        if chargepoint.data["set"]["current"] == 0:
                            continue
                    if chargepoint.data["set"]["charging_ev"] != -1:
                        charging_ev = chargepoint.data["set"]["charging_ev"]
                        if((charging_ev.charge_template.data["prio"] == prio) and 
                                (charging_ev.charge_template.data["chargemode"]["selected"] == mode or mode == None) and 
                                (charging_ev.data["control_parameter"]["chargemode"] == submode) and
                                (chargepoint.data["set"]["charging_ev"].data["control_parameter"]["required_current"] > chargepoint.data["set"]["current"])):
                            valid_chargepoints[chargepoint] = None
            preferenced_chargepoints = self._get_preferenced_chargepoint(valid_chargepoints, False)

            if len(preferenced_chargepoints) != 0:
                log.message_debug_log("debug", "## Ladepunkte, die nicht mit Maximalstromstaerke laden, wieder hochregeln.")
                for cp in preferenced_chargepoints:
                    missing_current = cp.data["set"]["charging_ev"].data["control_parameter"]["required_current"] - cp.data["set"]["current"]
                    # Wenn der LP erst in diesem Zyklus eingeschaltet wird, sind noch keine phases_in_use hinterlegt.
                    if cp.data["get"]["phases_in_use"] == 0:
                        phases = cp.data["set"]["phases_to_use"]
                    else:
                        phases = cp.data["get"]["phases_in_use"]
                    required_power = 230 * phases * missing_current
                    # Lastmanagement für den zusätzlichen Ladestrom durchführen
                    loadmanagement_state, overloaded_counters = loadmanagement.loadmanagement_for_cp(cp, required_power, missing_current, phases)
                    if loadmanagement_state == True:
                        overloaded_counters = sorted(overloaded_counters.items(), key=lambda e: e[1][1], reverse = True)
                        # Wenn max_overshoot_phase 0 ist, wurde die maximale Gesamtleistung überschrittten und max_current_overshoot muss, 
                        # wenn weniger als 3 Phasen genutzt werden, entsprechend dividiert werden.
                        if overloaded_counters[0][1][1] == 0 and phases < 3:
                            undo_missing_current = (overloaded_counters[0][1][0] * (3 - phases +1)) * -1
                        else:
                            undo_missing_current = overloaded_counters[0][1][0] * -1
                        required_power = 230 * phases * undo_missing_current

                        if loadmanagement.loadmanagement_for_cp(cp, required_power, undo_missing_current, phases) == True:
                            self._process_data(cp, cp.data["set"]["current"] + missing_current + undo_missing_current, phases)
                            if missing_current + undo_missing_current > 0.01:
                                log.message_debug_log("debug", "Ladung an LP"+str(cp.cp_num)+" um "+str(missing_current)+"A angepasst.")
                    else:
                        self._process_data(cp, cp.data["set"]["current"] + missing_current, phases)
                        log.message_debug_log("debug", "Ladung an LP"+str(cp.cp_num)+" um "+str(missing_current)+"A angepasst.")
                data.counter_data["counter0"].print_stats()
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
                    if chargepoint.data["get"]["charge_state"] == False:
                        continue
                    if chargepoint.data["set"]["charging_ev"] != -1:
                        charging_ev = chargepoint.data["set"]["charging_ev"]
                        if( (charging_ev.charge_template.data["prio"] == prio) and 
                            (charging_ev.charge_template.data["chargemode"]["selected"] == mode or mode == None) and 
                            (charging_ev.data["control_parameter"]["chargemode"] == submode)):
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
        overloaded_counters = None
        try:
            charging_ev = chargepoint.data["set"]["charging_ev"]
            phases = self._get_phases(chargepoint)
            required_current = charging_ev.data["control_parameter"]["required_current"]
            required_power = phases * 230 * \
                charging_ev.data["control_parameter"]["required_current"]
            pub.pub("openWB/set/chargepoint/"+str(chargepoint.cp_num)+"/set/required_power", required_power)
            chargepoint.data["set"]["required_power"] = required_power
            if charging_ev.data["control_parameter"]["chargemode"] == "pv_charging":
                self._calc_pv_charging(chargepoint, required_power,
                                required_current, phases)
            elif (charging_ev.data["control_parameter"]["chargemode"] == "stop" or (charging_ev.data["control_parameter"]["chargemode"] == "standby")):
                required_current, phases = no_load()
                self._process_data(chargepoint, required_current, phases)
            else:
                overloaded_counters = self._calc_normal_load(chargepoint, required_power,
                                    required_current, phases)
            return overloaded_counters
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
            required_current, phases, overloaded_counters = allocate_power(chargepoint, required_power, required_current, phases)
            if data.counter_data["all"].data["set"]["loadmanagement"] == True:
                required_current = 0
            self._process_data(chargepoint, required_current, phases)
            return overloaded_counters
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
            if (chargepoint.data["set"]["charging_ev"].charge_template.data["chargemode"]["selected"] == "scheduled_charging" and 
                    "pv_charging" not in chargepoint.data["set"]["charging_ev"].charge_template.data["chargemode"]):
                required_current, phases = no_load()
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
                    if "cp" in cp:
                        if data.cp_data[cp].data["set"]["charging_ev"]!= -1:
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
            if data.pv_data["all"].overhang_left() != 0:
                if data.pv_data["all"].overhang_left() > 0:
                    self._distribution(False)
                if (data.pv_data["all"].overhang_left() - data.general_data["general"].data["chargemode_config"]["pv_charging"]["feed_in_yield"]) > 0:
                    self._distribution(True)
            data.pv_data["all"].put_stats()
        except Exception as e:
            log.exception_logging(e)

    def _reduce_used_evu_overhang(self):
        """ prüft, ob für LP ohne Einspeisungsgrenze noch EVU-Überschuss zurückgenommen werden muss und dann für die LP mit Einspeiungsgrenze.
        """
        try:
            if data.pv_data["all"].overhang_left != 0:
                if data.pv_data["all"].overhang_left() < 0:
                    self._distribution(True)
                if (data.pv_data["all"].overhang_left() - data.general_data["general"].data["chargemode_config"]["pv_charging"]["feed_in_yield"]) < 0:
                    self._distribution(False)
            data.pv_data["all"].put_stats()
        except Exception as e:
            log.exception_logging(e)

    def _distribution(self, feed_in_limit):
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
                if "cp" in chargepoint:
                    if data.cp_data[chargepoint].data["set"]["charging_ev"] != -1:
                        charging_ev = data.cp_data[chargepoint].data["set"]["charging_ev"]
                        if charging_ev.data["control_parameter"]["chargemode"] == "pv_charging":
                            if (data.cp_data[chargepoint].data["set"]["current"] != 0 and 
                                    charging_ev.charge_template.data["chargemode"]["pv_charging"]["feed_in_limit"] == feed_in_limit):
                                num_of_phases += data.cp_data[chargepoint].data["set"]["phases_to_use"]
            # Ladung aktiv?
            if num_of_phases > 0:
                bat_overhang = data.bat_module_data["all"].data["set"]["charging_power_left"]
                if feed_in_limit == False:
                    # pos. Wert -> Ladestrom wird erhöht, negativer Wert -> Ladestrom wird reduziert
                    current_diff_per_phase = (data.pv_data["all"].overhang_left() + bat_overhang) / 230 / num_of_phases
                else:
                    feed_in_yield = data.general_data["general"].data["chargemode_config"]["pv_charging"]["feed_in_yield"]
                    if data.pv_data["all"].overhang_left() <= feed_in_yield:
                        # pos. Wert -> Ladestrom wird erhöht, negativer Wert -> Ladestrom wird reduziert
                        current_diff_per_phase = (data.pv_data["all"].overhang_left() - feed_in_yield + bat_overhang) / 230 / num_of_phases
                    else:
                        # Wenn die Einspeisungsgrenze erreicht wird, Strom schrittweise erhöhen, bis dies nicht mehr der Fall ist.
                        current_diff_per_phase = num_of_phases
                for cp in data.cp_data:
                   if "cp" in cp:
                        chargepoint = data.cp_data[cp]
                        if chargepoint.data["set"]["charging_ev"] != -1:
                            charging_ev = chargepoint.data["set"]["charging_ev"]
                            if charging_ev.charge_template.data["chargemode"]["selected"] == "pv_charging" or charging_ev.data["control_parameter"]["chargemode"] == "pv_charging":
                                if (chargepoint.data["set"]["current"] != 0 and 
                                        charging_ev.charge_template.data["chargemode"]["pv_charging"]["feed_in_limit"] == feed_in_limit):
                                    phases = chargepoint.data["set"]["phases_to_use"]
                                    # Einhalten des Mindeststroms des Lademodus und Maximalstroms des EV
                                    current = charging_ev.check_min_max_current_for_pv_charging(current_diff_per_phase+chargepoint.data["set"]["current"])
                                    power_diff = phases * 230 * (current - chargepoint.data["set"]["current"])
                                    
                                    if power_diff != 0:
                                        # Laden nur mit der Leistung, die vorher der Speicher bezogen hat
                                        if ( bat_overhang - power_diff) > 0:
                                            if data.bat_module_data["all"].allocate_bat_power(power_diff) == False:
                                                current = 0
                                        # Laden mit EVU-Überschuss und der Leistung, die vorher der Speicher bezogen hat
                                        elif bat_overhang > 0:
                                            pv_power = power_diff - bat_overhang
                                            if data.pv_data["all"].allocate_evu_power(pv_power) == False:
                                                current = 0
                                            elif data.bat_module_data["all"].allocate_bat_power(bat_overhang) == False:
                                                current = 0
                                        # Laden nur mit EVU-Überschuss bzw. Reduktion des EVU-Bezugs
                                        else:
                                            if data.pv_data["all"].allocate_evu_power(power_diff) == False:
                                                current = 0

                                    chargepoint.data["set"]["current"] = current
                                    log.message_debug_log("info", "Überschussladen an LP: "+str(chargepoint.cp_num)+", Ladestrom: "+str(current)+"A, Phasen: "+str(phases)+", Ladeleistung: "+str(phases * 230 * current)+"W")
        except Exception as e:
            log.exception_logging(e)

    def _check_auto_phase_switch(self):
        """ geht alle LP durch und prüft, ob eine Ladung aktiv ist, ob automatische Phasenumschaltung 
        möglich ist und ob ob ein Timer gestartet oder gestoppt werden muss oder ob ein Timer abgelaufen ist.
        """
        try:
            for cp in data.cp_data:
                if "cp" in cp:
                    if data.cp_data[cp].data["set"]["charging_ev"] != -1:
                        chargepoint = data.cp_data[cp]
                        if chargepoint.data["config"]["auto_phase_switch_hw"] == True and chargepoint.data["get"]["charge_state"] == True:
                            chargepoint.data["set"]["phases_to_use"] = chargepoint.data["set"]["charging_ev"].auto_phase_switch(chargepoint.data["get"]["phases_in_use"], chargepoint.data["get"]["current"])
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
            data.pv_data["all"].put_stats()
        except Exception as e:
            log.exception_logging(e)

    def _get_bat_and_evu_overhang(self):
        """
        """
        return data.bat_module_data["all"].data["get"]["power"] + data.pv_data["all"].data["set"]["available_power"]


def allocate_power(chargepoint, required_power, required_current, phases):
    """allokiert, wenn vorhanden erst Speicherladeleistung, dann EVU-Überschuss 
    und dann EVU-Bezug im Lastamanagement.

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
    phases: int
        Phasen, mit denen geladen werden kann
    """
    try:
        bat_overhang = data.bat_module_data["all"].power_for_bat_charging()
        evu_overhang = data.pv_data["all"].overhang_left()
        remaining_required_power = required_power
        overloaded_counters = None
        # Wenn vorhanden, Speicherenergie allokieren.
        if bat_overhang > 0:
            if bat_overhang > required_power:
                to_allocate = required_power
                remaining_required_power = 0
            else:
                to_allocate = required_power - bat_overhang
                remaining_required_power = required_power - to_allocate
                if data.bat_module_data["all"].allocate_bat_power(to_allocate) == False:
                    required_current, phases= no_load()
        # Wenn vorhanden, EVU-Überschuss allokieren.
        if remaining_required_power > 0:
            if evu_overhang > 0:
                if evu_overhang > required_power:
                    to_allocate = required_power
                    remaining_required_power = 0
                else:
                    to_allocate = required_power - evu_overhang
                    remaining_required_power = required_power - to_allocate
                    if data.pv_data["all"].allocate_evu_power(to_allocate) == False:
                        required_current, phases= no_load()
        # Rest ermitteln und allokieren
        if remaining_required_power > 0:
            evu_current = remaining_required_power / (phases * 230)
            loadmanagement_state, overloaded_counters = loadmanagement.loadmanagement_for_cp(chargepoint, remaining_required_power, evu_current, phases)
            if loadmanagement_state == True:
                required_current = 0
        return required_current, phases, overloaded_counters
    except Exception as e:
        log.exception_logging(e)

def no_load():
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