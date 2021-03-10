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
        self.reserved_pv_power = 0
        self.pv_power_left = 0

    def calc_power_for_control(self):
        """ berechnet die Leistung, die von der PV-Anlage in der Regelung genutzt werden kann.
        Ein-/Ausschaltverzögerung: Erst wenn für eine bestimmte Zeit eine bestimmte Grenze über/unter-
            schritten wurde, wird die Ladung gestartet/gestoppt. So wird häufiges starten/stoppen 
            vermieden. Die Grenzen aus den Einstellungen sind als Deltas zu verstehen, die absoluten 
            Schaltpunkte ergeben sich aus der Einspeisungsgrenze oder dem Regelmodus.
        Einspeisungsgrenze: Meist darf nur bis zu einem bestimmten Ertrag eingespeist werden (70%). 
            Bei einem guten Ertrag wird dann nur der PV-Strom genutzt, der nicht ins Netz eingespeist 
            werden darf.
        Regelmodus: Wenn möglichst der ganze PV-Strom genutzt wird, sollte die EVU-Leistung irgendwo 
            im Bereich um 0 leigen. Um ein Aufschwingen zu vermeiden, sollte die verfügbare Leistung nur 
            angepasst werden, wenn sie außerhalb des Regelbereichs liegt.

        Return
        ------
        int: PV-Leistung, die genutzt werden darf (auf allen Phasen/je Phase unterschiedlich?)
        """
        try:
            self.reserved_pv_power = 0  # wird reserviert, wenn die Einschaltverzögerung startet
            # Initialer Aufruf
            if "set" not in self.data:
                self.data["set"] = {}
            if "get" not in self.data:
                self.data["get"] = {}
            if len(data.pv_data) > 1:
                self.data["config"]["configured"]=True
                if "available_power" not in self.data["set"]:
                    self.data["set"]["available_power"] = 0
                if "pv_power_left" not in self.data["get"]:
                    self.data["get"]["pv_power_left"] = 0
                # aktuelle Leistung an der EVU, enthält die Leistung der Einspeisungsgrenze
                used_power = self.data["set"]["available_power"] - self.data["get"]["pv_power_left"]
                evu_overhang = data.counter_data["evu"].data["get"]["power_all"] * (-1)
                
                # Regelmodus
                control_range_low = self.data["config"]["control_range"][0]
                control_range_high = self.data["config"]["control_range"][1]
                control_range_center = (control_range_high - control_range_low) / 2
                if control_range_low < evu_overhang < control_range_high:
                    available_power = used_power
                else:
                    available_power = used_power + evu_overhang - control_range_center

                if available_power < 0:
                    available_power = 0

                log.message_debug_log("debug", str(available_power)+"W PV-Leistung, die für die Regelung verfügbar ist")
            # nur allgemeiner PV-Key vorhanden, d.h. kein Modul konfiguriert
            else:
                self.data["config"]["configured"]=False
                available_power = 0 # normalisierte verfügbare Leistung, Regelpunkt ist in der Mitte des Regelintervalls
                log.message_debug_log("debug", "Kein PV-Modul konfiguriert.")
            self.pv_power_left = available_power
            self.data["set"]["available_power"] = available_power
            pub.pub("openWB/pv/set/available_power", available_power)
            pub.pub("openWB/pv/config/configured", self.data["config"]["configured"])

        except Exception as e:
            log.exception_logging(e)

    def _switch_on_off_pv_load(self, control_parameter, required_power, required_current, phases):
        """ prüft, ob die Einschaltschwelle erreicht wurde, reserviert Leistung und gibt diese frei 
        bzw. stoppt die Freigabe wenn die Ausschaltschwelle und -verzögerung erreicht wurde.

        Parameter
        ---------
        control_parameter: dict
            Regel-Parameter des Autos
        required_power: float
            Leistung, mit der geladen werden soll
        required_current: list
            Stromstärke, mit der geladen werden soll
        phases: int
            Phasen, mit denen geladen werden soll
        Return
        ------
        required_power: float
            Leistung, mit der geladen werden kann
        required_current: list
            Stromstärke, mit der geladen werden kann
        phases: int
            Phasen, mit denen geladen werden kann
        """
        pv_config = self.data["config"]
        if "pv_available_prev" not in control_parameter:
            control_parameter["pv_available_prev"] = False
        if control_parameter["pv_available_prev"] == False:
            if self.pv_power_left > pv_config["switch_on_threshold"]*phases:
                if "timestamp_switch_on_off" in pv_config:
                    if timecheck.check_timestamp(control_parameter["timestamp_switch_on_off"], pv_config["switch_on_delay"]) == True:
                        required_power = 0
                        required_current = [0] * phases
                        phases = 0
                    else:
                        control_parameter["pv_available_prev"] = True
                        control_parameter["timestamp_switch_on_off"] = ""
                        self.reserved_pv_power -= required_power
                        self.allocate_pv_power(required_power*-1)
                        log.message_debug_log("info", "Einschaltschwelle von "+str(pv_config["switch_on_threshold"])+ "für die Dauer der Einschaltverzögerung überschritten.")
                else:
                    control_parameter["timestamp_switch_on_off"] = timecheck.create_timestamp()
                    required_power = 0
                    required_current = [0] * phases
                    phases = 0
                    self.reserved_pv_power += required_power
                    self.allocate_pv_power(required_power)
                    log.message_debug_log("info", "Einschaltverzögerung für "+str(pv_config["switch_on_delay"])+ "s aktiv.")
            else:
                required_power = 0
                required_current = [0] * phases
                phases = 0
        else:
            evu_overhang = data.counter_data["evu"].data["get"]["power_all"] * (-1)
            # Einspeisungsgrenze (Verschiebung des Regelpunkts)
            if data.pv_data["pv"].data["config"]["feed_in_yield_active"] == True:
                evu_overhang -= data.pv_data["pv"].data["config"]["feed_in_yield"]
            if evu_overhang < (pv_config["switch_off_threshold"]*(-1)):
                if "timestamp_switch_on_off" in control_parameter:
                    if timecheck.check_timestamp(control_parameter["timestamp_switch_on_off"], pv_config["switch_off_delay"]) == False:
                        control_parameter["pv_available_prev"] = False
                        control_parameter["timestamp_switch_on_off"] = ""
                        required_power = 0
                        required_current = [0] * phases
                        phases = 0
                        log.message_debug_log("info", "Abschaltschwelle von "+str(pv_config["switch_off_threshold"])+"für die Dauer der Abschaltverzögerung unterschritten.")
                else:
                    control_parameter["timestamp_switch_on_off"] = timecheck.create_timestamp()
                    log.message_debug_log("info", "Abschaltverzögerung für "+ str(pv_config["switch_off_delay"])+"s aktiv.")
        return required_power, required_current, phases

    def power_for_pv_load(self, feed_in_yield_active):
        """ gibt die verfügbare PV-Leistung unter Berücksichtigung der Einspeisungsgrenze zurück.

        Paramter
        --------
        feed_in_limit_active: bool
            soll die Einspeisungsgrenze berücksichtigt werden.

        Return
        ------
        pv_power_left: int
            verfügbare PV-Leistung
        """
        if self.data["config"]["configured"] == True:
            # Einspeisungsgrenze (Verschiebung des Regelpunkts)
            if self.data["config"]["feed_in_yield_active"] == True:
                remaining_power = self.pv_power_left - self.data["config"]["feed_in_yield"]
                if remaining_power > 0:
                    return remaining_power
                else:
                    return 0
            else:
                return self.pv_power_left

        else:
            log.message_debug_log("warning", "PV-Laden aktiv, obwohl kein PV-Modul konfiguriert wurde.")
            return 0
    # return available pv power with feed in yield

    def power_for_normal_load(self):
        """ gibt die verfügbare PV-Leistung zurück.

        Return
        ------
        pv_power_left: int
            verfügbare PV-Leistung
        """
        if self.data["config"]["configured"] == True:
            return self.pv_power_left
        else:
            return 0
    # return available pv power without feed in yield

    def allocate_pv_power(self, required_power):
        """ subtrahieren der zugeteilten Leistung von der verfügbaren PV-Leistung

        Parameter
        ---------
        required_power: float
            Leistung, mit der geladen werden soll
        """
        if self.data["config"]["configured"] == True:
            self.pv_power_left -= required_power
            if self.pv_power_left < 0:
                pass #error

    def adapt_current(self, required_power, required_current, phases, control_parameter, max_current_ev, min_current_ev):
        """ anpassen der Leistung für ein EV, wenn die PV-Leistung nicht mehr ausreicht. Prüfen, der Ein-und Ausschaltschwellen/timer.

        Parameter
        ---------
        required_power: float
            Leistung, mit der geladen werden soll
        required_current: list
            Stromstärke, mit der geladen werden soll
        phases: int
            Phasen, mit denen geladen werden soll
        control_paramter: dict
            Regel-Parameter des Autos
        max_current: int
            Maximale Stromstärke, mit der das EV geladen werden darf
        min_current: int
            Minimale Stromstärke, mit der das EV geladen werden muss

        Return
        ------
        required_power: float
            Leistung, mit der geladen werden kann
        required_current: list
            Stromstärke, mit der geladen werden kann
        phases: int
            Phasen, mit denen geladen werden kann
        """
        # Hoch/Runterregeln im Bereich der min/maximalen Stromstärke des Autos, das Stoppen der PV-Ladung darf nur durch _switch_on_off_pv_load erfolgen.
        if (self.pv_power_left - required_power) > 0:
            pass
            # todo hochregeln
        else:
            pass
            # todo runterregeln
        # Ein-/Ausschaltverzögerung
        required_power, required_current, phases = self._switch_on_off_pv_load(control_parameter, required_power, required_current, phases)
        if (self.pv_power_left - required_power) < 0:
            evu_power = self.pv_power_left *-1 # muss bezogen werden
            pv_power = required_power - evu_power
            evu_current = required_power / (phases * 230)
            evu_current_phases = [evu_current]*phases
            if evu_power > 0:
                if loadmanagement.loadmanagement(evu_power, evu_current_phases) == True:
                    self.allocate_pv_power(pv_power)
                    return required_power, required_current, phases
                else:
                    pass
                    # todo
        else:
            self.allocate_pv_power(required_power)
            return required_power, required_current, phases

        return required_power, required_current, phases, evu_power

    def put_stats(self):
        """ Publishen und Loggen der verbleibnden PV-Leistung und reservierten Leistung
        """
        if data.pv_data["pv"].data["config"]["configured"] == True:
            pub.pub("openWB/pv/get/pv_power_left", self.pv_power_left)
            log.message_debug_log("debug", "Fuer die folgenden Algorithmus-Durchlaeufe verbleibende PV-Leistung "+str(self.pv_power_left)+"W, zusätzllich reservierte Leistung "+str(self.reserved_pv_power)+"W")

class pvModule():
    """
    """

    def __init__(self):
        self.data = {}
    """
    """
