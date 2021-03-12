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
                used_power = data.cp_data["all"].data["get"]["power_all"]
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

                log.message_debug_log("debug", str(available_power)+"W EVU-Überschuss, der für die Regelung verfügbar ist, davon "+str(self.data["get"]["reserved_pv_power"])+"W für die Einschaltverzögerung reservierte Leistung.")
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

    def switch_on_off(self, chargepoint, required_power, required_current, phases):
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
        control_parameter = chargepoint.data["set"]["charging_ev"].data["control_parameter"]
        # verbleibender EVU-Überschuss unter Berücksichtigung der Einspeisungsgrenze
        overhang_power_left_feed_in = self.power_for_pv_load(chargepoint.data["set"]["charging_ev"].charge_template.data["chargemode"]["pv_load"]["feed_in_limit"])
        if control_parameter["pv_available_prev"] == False:
            if "timestamp_switch_on_off" in control_parameter:
                if overhang_power_left_feed_in > 0:
                    if timecheck.check_timestamp(control_parameter["timestamp_switch_on_off"], pv_config["switch_on_delay"]) == True:
                        required_power = 0
                    else:
                        control_parameter["pv_available_prev"] = True
                        control_parameter["timestamp_switch_on_off"] = ""
                        self.data["get"]["reserved_pv_power"] -= required_power
                        log.message_debug_log("info", "Einschaltschwelle von "+str(pv_config["switch_on_threshold"])+ "für die Dauer der Einschaltverzögerung überschritten.")
                else:
                    control_parameter["timestamp_switch_on_off"] = ""
                    self.data["get"]["reserved_pv_power"] -= required_power
                    log.message_debug_log("info", "Einschaltschwelle von "+str(pv_config["switch_on_threshold"])+ "während der Einschaltverzögerung unterschritten.")
            else:
                if overhang_power_left_feed_in > pv_config["switch_on_threshold"]*phases:
                    control_parameter["timestamp_switch_on_off"] = timecheck.create_timestamp()
                    self.data["get"]["reserved_pv_power"] += required_power
                    log.message_debug_log("info", "Einschaltverzögerung für "+str(pv_config["switch_on_delay"])+ "s aktiv.")
                    required_power = 0
                else:
                    required_power = 0
        else:
            if overhang_power_left_feed_in < (pv_config["switch_off_threshold"]*(-1)):
                if "timestamp_switch_on_off" in control_parameter:
                    if timecheck.check_timestamp(control_parameter["timestamp_switch_on_off"], pv_config["switch_off_delay"]) == False:
                        control_parameter["pv_available_prev"] = False
                        control_parameter["timestamp_switch_on_off"] = ""
                        required_power = 0
                        log.message_debug_log("info", "Abschaltschwelle von "+str(pv_config["switch_off_threshold"])+"W für die Dauer der Abschaltverzögerung unterschritten.")
                else:
                    control_parameter["timestamp_switch_on_off"] = timecheck.create_timestamp()
                    log.message_debug_log("info", "Abschaltverzögerung für "+ str(pv_config["switch_off_delay"])+"s aktiv.")
        pub.pub_dict("openWB/vehicle/"+str(chargepoint.data["set"]["charging_ev"].ev_num)+"/control_parameter", control_parameter)

        # nur durch die Ausschaltverzögerung darf required_power auf 0 gesetzt werden, sonst muss bezogen werden.
        if required_power != 0:
            if (overhang_power_left_feed_in - required_power) < 0:
                evu_power = overhang_power_left_feed_in *-1 # muss bezogen werden
                pv_power = required_power - evu_power
                evu_current = required_power / (phases * 230)
                evu_current_phases = [evu_current]*phases
                if evu_power > 0:
                    if loadmanagement.loadmanagement(evu_power, evu_current_phases) == True:
                        self.allocate_pv_power(pv_power)
                    else:
                        pass
                        # todo
            else:
                self.allocate_pv_power(required_power)
        else:
            required_current = [0] * phases
            phases = 0

        return required_power, required_current, phases

    def power_for_pv_load(self, feed_in_yield_active):
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

    def power_for_normal_load(self):
        """ gibt den verfügbaren EVU-Überschuss zurück.

        Return
        ------
        overhang_power_left: int
            verfügbare PV-Leistung
        """
        if self.data["config"]["configured"] == True:
            return (self.data["get"]["overhang_power_left"] - self.data["get"]["reserved_pv_power"])
        else:
            return 0
    # return available pv power without feed in yield

    def allocate_pv_power(self, required_power):
        """ subtrahieren der zugeteilten Leistung vomverfügbaren EVU-Überschuss

        Parameter
        ---------
        required_power: float
            Leistung, mit der geladen werden soll
        """
        if self.data["config"]["configured"] == True:
            self.data["get"]["overhang_power_left"] -= required_power
            if self.data["get"]["overhang_power_left"] < 0:
                pass #error

    def put_stats(self):
        """ Publishen und Loggen des verbleibnden EVU-Überschusses und reservierten Leistung
        """
        pub.pub("openWB/pv/config/configured", self.data["config"]["configured"])
        if self.data["config"]["configured"] == True:
            pub.pub("openWB/pv/get/overhang_power_left", self.data["get"]["overhang_power_left"])
            pub.pub("openWB/pv/get/reserved_pv_power", self.data["get"]["reserved_pv_power"])
            log.message_debug_log("debug", str(self.data["get"]["overhang_power_left"])+"W EVU-Überschuss, der fuer die folgenden Ladepunkte uebrig ist, davon "+str(self.data["get"]["reserved_pv_power"])+"W für die Einschaltverzögerung reservierte Leistung.")

class pvModule():
    """
    """

    def __init__(self):
        self.data = {}
    """
    """
