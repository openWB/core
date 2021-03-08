""" Algrithmus zur Berechnung der Ladeströme
"""

import data
import log
import pub
import timecheck


class control():
    """Verteilung des Stroms auf die Ladepunkte
    """

    def __init__(self):
        self.reserved_pv_power = 0

    def calc_current(self):
        """ Einstiegspunkt in den Regel-Algorithmus
        ruft in der Reihenfolge der Prioritäten der Lademodi die Berechnungsfunktion auf.
        """
        # Zählvariablen vor dem Start der Regelung zurücksetzen
        try:
            if data.pv_data["pv"].data["config"]["configured"] == True:
                data.pv_data["pv"].data["get"]["pv_power_left"] = data.pv_data["pv"].data["set"]["available_power"]
                self.reserved_pv_power = 0  # wird reserviert, wenn die Einschaltverzögerung startet
            data.counter_data["evu"].data["set"]["consumption_left"] = data.counter_data["evu"].data["config"]["max_consumption"]
            data.counter_data["evu"].data["set"]["current_left"] = data.counter_data["evu"].data["config"]["max_current"]
        except KeyError as key:
            print("dictionary key",key,"doesn't exist in calc_current")
        
        self._calc_cp_in_specified_mode("scheduled_load", "instant_load")
        self._calc_cp_in_specified_mode("time_load", "time_load")
        self._calc_cp_in_specified_mode("instant_load", "instant_load")
        self._calc_cp_in_specified_mode("pv_load", "instant_load")
        self._calc_cp_in_specified_mode("scheduled_load", "pv_load")
        self._calc_cp_in_specified_mode("pv_load", "pv_load")

    def _calc_cp_in_specified_mode(self, mode, submode):
        """ berechnet die Zuteilung für die Ladepunkte, bei denen der angebenene Lademodus und der Lademodus, 
        der aufgrund des Zustands des eingestellten Lademodus benötigt wird, aktiv sind. Zuerst für die Lade-
        punkte mit Priorität, dann für die Ladepunkte ohne Priorität.

        Parameter
        ---------
        mode: str
            Lademodus, der am Ladepunkt eingestellt ist

        submode: str
            Lademodus, der aufgrund des Zustands des eingestellten Lademodus benötigt wird
        """
        for chargepoint in data.cp_data:
            if "charging_ev" in data.cp_data[chargepoint].data:
                charging_ev = data.cp_data[chargepoint].data["set"]["charging_ev"]
                if (charging_ev.charge_template.data["prio"] == True) and (charging_ev.charge_template.data["chargemode"]["selected"] == mode) and (charging_ev.data["control_parameter"]["chargemode"] == submode):
                    self._start_indiviual_calc(data.cp_data[chargepoint])

        for chargepoint in data.cp_data.keys():
            if "charging_ev" in data.cp_data[chargepoint].data:
                charging_ev = data.cp_data[chargepoint].data["set"]["charging_ev"]
                if (charging_ev.charge_template.data["prio"] == False) and (charging_ev.charge_template.data["chargemode"]["selected"] == mode) and (charging_ev.data["control_parameter"]["chargemode"] == submode):
                    self._start_indiviual_calc(data.cp_data[chargepoint])

    def _start_indiviual_calc(self, chargepoint):
        """ ermittelt die konfigurierte Anzahl Phasen, Stromstärke und Leistung.

        Parameter
        ---------
        chargepoint: dict
            Daten des Ladepunkts
        Return
        ------
        """
        charging_ev = chargepoint.data["set"]["charging_ev"]
        required_current = []
        phases = self._get_phases(chargepoint)
        for n in range(phases):
            required_current.append(
                charging_ev.data["control_parameter"]["required_current"])
        required_power = phases * 230 * \
            charging_ev.data["control_parameter"]["required_current"]
        if charging_ev.data["control_parameter"]["chargemode"] == "pv_load":
            self._calc_pv_load(chargepoint, required_power,
                              required_current, phases)
        else:
            self._calc_normal_load(chargepoint, required_power,
                                  required_current, phases)

    def _calc_normal_load(self, chargepoint, required_power, required_current, phases):
        """ prüft, ob mit PV geladen werden kann oder bezogen werden muss.

        Parameter
        ---------
        chargepoint: dict
            Daten des Ladepunkts
        required_power: float
            Leistung, mit der geladen werden soll
        required_current: list
            Stromstärke, mit der geladen werden soll
        phases: int
            Phasen, mit denen geladen werden soll
        Return
        ------
        """
        # PV-Strom nutzen
        if data.pv_data["pv"].data["config"]["configured"] == True:
            if data.pv_data["pv"].data["set"]["available_power"] > data.pv_data["pv"].data["config"]["control_range"][0]:
                pv_power_left = data.pv_data["pv"].data["get"]["pv_power_left"] - self.reserved_pv_power
                pv_power_left -= required_power
                if pv_power_left > 0:
                    self._process_data(chargepoint, required_power, required_current, phases)
                else:
                    evu_power = pv_power_left *-1 # muss bezogen werden
                    pv_power = required_power - evu_power
                    evu_current = required_power / (phases * 230)
                    evu_current_phases = []
                    for n in range(phases):
                        evu_current_phases.append(evu_current)
                    if self._loadmanagement(evu_power, evu_current_phases) == True:
                        self._process_data(chargepoint, pv_power, required_current, phases)
                return
        # Bezug
        if self._loadmanagement(required_power, required_current) == True:
            self._process_data(chargepoint, required_power, required_current, phases)

    def _calc_pv_load(self, chargepoint, required_power, required_current, phases):
        """prüft, ob Speicher oder EV Vorrang hat und wie viel Strom/Leistung genutzt werden kann.

        Parameter
        ---------
        chargepoint: dict
            Daten des Ladepunkts
        required_power: float
            Leistung, mit der geladen werden soll
        required_current: list
            Stromstärke, mit der geladen werden soll
        phases: int
            Phasen, mit denen geladen werden soll
        Return
        ------
        """
        if data.pv_data["pv"].data["config"]["configured"] == True:
            bat_charging_power_left = data.bat_module_data["bat"].data["set"]["charging_power_left"]
            if chargepoint.data["set"]["charging_ev"].charge_template["chargemode"]["selected"] == "scheduled_load" and "pv_load" not in chargepoint.data["set"]["charging_ev"].charge_template["chargemode"]:
                required_power, required_current, phases = self._no_pv_load(required_power, required_current, phases)
                log.message_debug_log("warning", "PV-Laden im Modus Zielladen aktiv und es wurden keine Einstellungen für PV-Laden konfiguriert.")
            else:
                # EV hat Vorrang
                if (chargepoint.data["set"]["charging_ev"].charge_template["chargemode"]["pv_load"]["bat_prio"] == False) and (bat_charging_power_left > 0):
                    # Laden nur mit der Leistung, die vorher der Speicher bezogen hat
                    if ( bat_charging_power_left - required_power) > 0:
                        bat_charging_power_left -= required_power 
                    # Laden mit PV-Leistung und der Leistung, die vorher der Speicher bezogen hat
                    elif data.pv_data["pv"].data["set"]["available_power"] > data.pv_data["pv"].data["config"]["control_range"][0]:
                        pv_power = required_power - bat_charging_power_left
                        required_power, required_current, phases = self._adapt_current(chargepoint, pv_power, required_current, phases)
                        bat_charging_power_left = 0
                    else:
                        # keine Leistung übrig
                        required_power, required_current, phases = self._no_pv_load(required_power, required_current, phases)
                # Speicher hat Vorrang, aber es wird noch eingespeist
                elif data.pv_data["pv"].data["set"]["available_power"] > data.pv_data["pv"].data["config"]["control_range"][0]:
                    required_power, required_current, phases = self._adapt_current(chargepoint, required_power, required_current, phases)
                else:
                    # Speicher zieht gesamte PV-Leistung und hat Vorrang -> keine Ladung
                    required_power, required_current, phases = self._no_pv_load(required_power, required_current, phases)
        else:
            required_power, required_current, phases = self._no_pv_load(required_power, required_current, phases)
            log.message_debug_log("warning", "PV-Laden aktiv, obwohl kein PV-Modul konfiguriert wurde.")
        self._process_data(chargepoint, required_power, required_current, phases)

    def _switch_on_off_pv_load(self, chargepoint, required_power, required_current, phases, pv_power_left):
        """ prüft, ob die Einschaltschwelle erreicht wurde, reserviert Leistung und gibt diese frei 
        bzw. stoppt die Freigabe wenn die Ausschaltschwelle und -verzögerung erreicht wurde.

        Parameter
        ---------
        chargepoint: dict
            Daten des Ladepunkts
        required_power: float
            Leistung, mit der geladen werden soll
        required_current: list
            Stromstärke, mit der geladen werden soll
        phases: int
            Phasen, mit denen geladen werden soll
        pv_power_left:
            PV-Leistung, die noch zur Verfügung steht.
        Return
        ------
        """
        control_parameter = chargepoint.data["set"]["charging_ev"].data["control_parameter"]
        pv_config = data.pv_data["pv"].data["config"]
        if control_parameter["pv_available_prev"] == False:
            if pv_power_left > pv_config["switch_on_threshold"]*phases:
                if "timestamp_switch_on_off" in pv_config:
                    if timecheck.check_timestamp(control_parameter["timestamp_switch_on_off"], pv_config["switch_on_delay"]) == True:
                        required_power, required_current, phases = self._no_pv_load(required_power, required_current, phases)
                    else:
                        control_parameter["pv_available_prev"] = True
                        control_parameter["timestamp_switch_on_off"] = ""
                        self.reserved_pv_power -= required_power
                        log.message_debug_log("info", "Einschaltschwelle von "+str(pv_config["switch_on_threshold"])+ "für die Dauer der Einschaltverzögerung überschritten.")
                else:
                    control_parameter["timestamp_switch_on_off"] = timecheck.create_timestamp()
                    required_power, required_current, phases = self._no_pv_load(required_power, required_current, phases)
                    self.reserved_pv_power += required_power
                    log.message_debug_log("info", "Einschaltverzögerung für "+str(pv_config["switch_on_delay"])+ "s aktiv.")
            else:
                required_power, required_current, phases = self._no_pv_load(required_power, required_current, phases)
        else:
            if required_power < (pv_config["switch_off_threshold"]*(-1)):
                if "timestamp_switch_on_off" in control_parameter:
                    if timecheck.check_timestamp(control_parameter["timestamp_switch_on_off"], pv_config["switch_off_delay"]) == False:
                        control_parameter["pv_available_prev"] = False
                        control_parameter["timestamp_switch_on_off"] = ""
                        required_power, required_current, phases = self._no_pv_load(required_power, required_current, phases)
                        log.message_debug_log("info", "Abschaltschwelle von "+str(pv_config["switch_off_threshold"])+"für die Dauer der Abschaltverzögerung unterschritten.")
                else:
                    control_parameter["timestamp_switch_on_off"] = timecheck.create_timestamp()
                    log.message_debug_log("info", "Abschaltverzögerung für "+ str(pv_config["switch_off_delay"])+"s aktiv.")
        return required_power, required_current, phases

    def _adapt_current(self, chargepoint, required_power, required_current, phases):
        """ regelt je nach vorhandener PV-Leistung hoch oder runter.

        Parameter
        ---------
        chargepoint: dict
            Daten des Ladepunkts
        required_power: float
            Leistung, mit der geladen werden soll
        required_current: list
            Stromstärke, mit der geladen werden soll
        phases: int
            Phasen, mit denen geladen werden soll
        Return
        ------
        released_power: float
            Leistung, die geladen werden darf
        """
        pv_power_left = data.pv_data["pv"].data["get"]["pv_power_left"] - self.reserved_pv_power
        if (pv_power_left - required_power) > 0:
            pass
            # todo hochregeln
        else:
            pass
            # todo runterregeln
        # Ein-/Ausschaltverzögerung
        required_power, required_current, phases = self._switch_on_off_pv_load(chargepoint, required_power, required_current, phases, pv_power_left)
        return required_power, required_current, phases

    def _loadmanagement(self, required_power, required_current):
        """ prüft, ob maximale Stromstärke oder Bezug überschritten wurden.

        Parameter
        ---------

        Return
        ------
        """
        # Maximale Leistung
        state = False
        consumption_left = data.counter_data["evu"].data["set"]["consumption_left"] - required_power
        if consumption_left > 0:
            state = True
        else:
            pass
            # runterregeln

        # Maximaler Strom
        current_left = []
        for n in range(len(required_current)):
            current_left.append(data.counter_data["evu"].data["set"]["current_left"][n] - required_current[n])
            if current_left[n] > 0:
                state = True
            else:
                # runterregeln
                break
        
        # Werte bei erfolgreichem Lastamanagement schreiben
        if state == True:
            data.counter_data["evu"].data["set"]["consumption_left"] = consumption_left
            for n in range (len(required_current)):
                data.counter_data["evu"].data["set"]["current_left"][n] = current_left[n]
        return state

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

    def _no_pv_load(self, required_power, required_current, phases):
        """ setzt die Parameter zum Stoppen der PV-Ladung

        Parameter
        ---------
        required_power: float
            Leistung, mit der geladen werden soll
        required_current: list
            Stromstärke, mit der geladen werden soll
        phases: int
            Phasen, mit denen geladen werden soll
        Return
        ------
        required_power: float
            Leistung, mit der geladen werden soll
        required_current: list
            Stromstärke, mit der geladen werden soll
        phases: int
            Phasen, mit denen geladen werden soll
        """
        required_power = 0
        for n in range(phases):
            required_current[n] = 0
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
        required_current: list
            Stromstärke, mit der geladen werden soll
        phases: int
            Phasen, mit denen geladen werden soll
        """
        data.pv_data["pv"].data["get"]["pv_power_left"] -= required_power
        chargepoint.data["set"]["current"] = required_current
        chargepoint.data["set"]["phases_to_use"] = phases
        pub.pub("openWB/pv/get/pv_power_left", data.pv_data["pv"].data["get"]["pv_power_left"])
        pub.pub("openWB/chargepoint/"+str(chargepoint.cp_num)+"/set/current", required_current)
        pub.pub("openWB/chargepoint/"+str(chargepoint.cp_num)+"/set/phases_to_use", phases)
        charging_ev = chargepoint.data["set"]["charging_ev"]
        log.message_debug_log("debug", "Algorithmus-Durchlauf für LP"+str(chargepoint.cp_num)+" beendet. Lademodus: "+charging_ev.charge_template.data["chargemode"]["selected"]+", Submodus: "+charging_ev.data["control_parameter"]["chargemode"]+", Priorität: "+str(charging_ev.charge_template.data["prio"]))
        log.message_debug_log("debug", "Fuer die folgenden Algorithmus-Durchlaeufe verbleibende PV-Leistung "+str(data.pv_data["pv"].data["get"]["pv_power_left"])+"W")
        log.message_debug_log("info", "LP: "+str(chargepoint.cp_num)+", Ladestrom: "+str(required_current)+"A, Phasen: "+str(phases)+", Ladeleistung: "+str(required_power)+"W")
