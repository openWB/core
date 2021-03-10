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
        # Zählvariablen vor dem Start der Regelung zurücksetzen
        try:
            if data.counter_data["evu"].data["get"]["power_all"] > 0: #Import
                data.counter_data["evu"].data["set"]["consumption_left"] = data.counter_data["evu"].data["config"]["max_consumption"] - data.counter_data["evu"].data["get"]["power_all"]
                data.counter_data["evu"].data["set"]["current_left"] = [m - n for m,n in zip(data.counter_data["evu"].data["config"]["max_current"], data.counter_data["evu"].data["get"]["current"])]
            else: # Export
                data.counter_data["evu"].data["set"]["consumption_left"] = data.counter_data["evu"].data["config"]["max_consumption"]
                data.counter_data["evu"].data["set"]["current_left"] = data.counter_data["evu"].data["config"]["max_current"]
        except Exception as e:
            log.exception_logging(e)

        self._calc_cp_in_specified_mode("scheduled_load", "instant_load")
        self._calc_cp_in_specified_mode(None, "time_load")
        self._calc_cp_in_specified_mode("instant_load", "instant_load")
        self._calc_cp_in_specified_mode("pv_load", "instant_load")
        self._calc_cp_in_specified_mode("scheduled_load", "pv_load")
        self._calc_cp_in_specified_mode("pv_load", "pv_load")
        self._calc_cp_in_specified_mode(None, "standby")
        self._calc_cp_in_specified_mode(None, "stop")

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
        try:
            for chargepoint in data.cp_data:
                if "set" in data.cp_data[chargepoint].data:
                    if "charging_ev" in data.cp_data[chargepoint].data["set"]:
                        charging_ev = data.cp_data[chargepoint].data["set"]["charging_ev"]
                        if mode == None:
                            if(charging_ev.charge_template.data["prio"] == True) and (charging_ev.data["control_parameter"]["chargemode"] == submode):
                                self._start_indiviual_calc(data.cp_data[chargepoint])
                        elif (charging_ev.charge_template.data["prio"] == True) and (charging_ev.charge_template.data["chargemode"]["selected"] == mode) and (charging_ev.data["control_parameter"]["chargemode"] == submode):
                            self._start_indiviual_calc(data.cp_data[chargepoint])

            for chargepoint in data.cp_data.keys():
                if "set" in data.cp_data[chargepoint].data:
                    if "charging_ev" in data.cp_data[chargepoint].data["set"]:
                        charging_ev = data.cp_data[chargepoint].data["set"]["charging_ev"]
                        if mode == None:
                            if(charging_ev.charge_template.data["prio"] == False) and (charging_ev.data["control_parameter"]["chargemode"] == submode):
                                self._start_indiviual_calc(data.cp_data[chargepoint])
                        elif (charging_ev.charge_template.data["prio"] == False) and (charging_ev.charge_template.data["chargemode"]["selected"] == mode) and (charging_ev.data["control_parameter"]["chargemode"] == submode):
                            self._start_indiviual_calc(data.cp_data[chargepoint])
        except Exception as e:
            log.exception_logging(e)

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
        phases = self._get_phases(chargepoint)
        required_current = [charging_ev.data["control_parameter"]["required_current"]] * phases
        required_power = phases * 230 * \
            charging_ev.data["control_parameter"]["required_current"]
        if charging_ev.data["control_parameter"]["chargemode"] == "pv_load":
            self._calc_pv_load(chargepoint, required_power,
                              required_current, phases)
        elif (charging_ev.data["control_parameter"]["chargemode"] == "stop" or (charging_ev.data["control_parameter"]["chargemode"] == "standby")):
            required_power, required_current, phases = self._no_load(chargepoint, required_power, required_current, phases)
            self._process_data(chargepoint, required_power, required_current, phases)
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
        pv_power_left = data.pv_data["pv"].power_for_normal_load()
        if pv_power_left > 0:
            pv_power_left -= required_power
            if pv_power_left > 0:
                data.pv_data["pv"].allocate_pv_power(required_power)
                self._process_data(chargepoint, required_power, required_current, phases)
            else:
                evu_power = pv_power_left *-1 # muss bezogen werden
                pv_power = required_power - evu_power
                evu_current = required_power / (phases * 230)
                evu_current_phases = [evu_current]*phases
                if loadmanagement.loadmanagement(evu_power, evu_current_phases) == True:
                    data.pv_data["pv"].allocate_pv_power(pv_power)
                    self._process_data(chargepoint, pv_power, required_current, phases)
            return
        # Bezug
        if loadmanagement.loadmanagement(required_power, required_current) == True:
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
        pv_power_left = data.pv_data["pv"].power_for_pv_load(chargepoint.data["set"]["charging_ev"].charge_template.data["chargemode"]["pv_load"]["feed_in_limit"])
        if pv_power_left > 0:
            bat_charging_power_left = data.bat_module_data["bat"].data["set"]["charging_power_left"]
            if chargepoint.data["set"]["charging_ev"].charge_template.data["chargemode"]["selected"] == "scheduled_load" and "pv_load" not in chargepoint.data["set"]["charging_ev"].charge_template.data["chargemode"]:
                required_power, required_current, phases = self._no_load(chargepoint, required_power, required_current, phases)
                log.message_debug_log("warning", "PV-Laden im Modus Zielladen aktiv und es wurden keine Einstellungen für PV-Laden konfiguriert.")
            else:
                # EV hat Vorrang
                if (chargepoint.data["set"]["charging_ev"].charge_template.data["chargemode"]["pv_load"]["bat_prio"] == False) and (bat_charging_power_left > 0):
                    # Laden nur mit der Leistung, die vorher der Speicher bezogen hat
                    if ( bat_charging_power_left - required_power) > 0:
                        bat_charging_power_left -= required_power 
                    # Laden mit PV-Leistung und der Leistung, die vorher der Speicher bezogen hat
                    elif pv_power_left > 0:
                        pv_power = required_power - bat_charging_power_left
                        required_power, required_current, phases = data.pv_data["pv"].adapt_current(pv_power, required_current, phases, chargepoint.data["set"]["charging_ev"].data["control_parameter"], chargepoint.data["set"]["charging_ev"].ev_template.data["max_current"], chargepoint.data["set"]["charging_ev"].ev_template.data["min_current"])
                        bat_charging_power_left = 0
                    else:
                        # keine Leistung übrig
                        required_power, required_current, phases = self._no_load(chargepoint, required_power, required_current, phases)
                # Speicher hat Vorrang, aber es wird noch eingespeist
                elif pv_power_left > 0:
                    required_power, required_current, phases = data.pv_data["pv"].adapt_current(required_power, required_current, phases, chargepoint.data["set"]["charging_ev"].data["control_parameter"], chargepoint.data["set"]["charging_ev"].ev_template.data["max_current"], chargepoint.data["set"]["charging_ev"].ev_template.data["min_current"])
                else:
                    # Speicher zieht gesamte PV-Leistung und hat Vorrang -> keine Ladung
                    required_power, required_current, phases = self._no_load(chargepoint, required_power, required_current, phases)
        else:
            required_power, required_current, phases = self._no_load(chargepoint, required_power, required_current, phases)
            log.message_debug_log("warning", "Keine PV-Leistung übrig.")
        data.pv_data["pv"].allocate_pv_power(required_power)
        self._process_data(chargepoint, required_power, required_current, phases)

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

    def _no_load(self, chargepoint, required_power, required_current, phases):
        """ setzt die Parameter zum Stoppen der PV-Ladung

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
        required_power: float
            Leistung, mit der geladen werden soll
        required_current: list
            Stromstärke, mit der geladen werden soll
        phases: int
            Phasen, mit denen geladen werden soll
        """
        required_power = 0
        required_current = [0] * phases
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
        chargepoint.data["set"]["current"] = required_current
        chargepoint.data["set"]["phases_to_use"] = phases
        pub.pub("openWB/chargepoint/"+str(chargepoint.cp_num)+"/set/current", required_current)
        pub.pub("openWB/chargepoint/"+str(chargepoint.cp_num)+"/set/phases_to_use", phases)
        charging_ev = chargepoint.data["set"]["charging_ev"]
        log.message_debug_log("debug", "Algorithmus-Durchlauf für LP"+str(chargepoint.cp_num)+" beendet. Lademodus: "+charging_ev.charge_template.data["chargemode"]["selected"]+", Submodus: "+charging_ev.data["control_parameter"]["chargemode"]+", Priorität: "+str(charging_ev.charge_template.data["prio"]))
        log.message_debug_log("info", "LP: "+str(chargepoint.cp_num)+", Ladestrom: "+str(required_current)+"A, Phasen: "+str(phases)+", Ladeleistung: "+str(required_power)+"W")
        log.message_debug_log("debug", "Fuer die folgenden Algorithmus-Durchlaeufe verbleibende EVU-Bezugs-Leistung "+str(data.counter_data["evu"].data["set"]["consumption_left"])+"W")
        data.pv_data["pv"].put_stats()