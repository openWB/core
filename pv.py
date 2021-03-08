"""PV-Logik
Die Leistung, die die PV-Module liefern, kann nicht komplett für das Laden und Smarthome verwendet werden. 
Davon ab geht z.B. noch der Hausverbrauch. Für das Laden mit PV kann deshalb nur der Strom verwendet werden, 
der sonst in das Netz eingespeist werden würde. 
"""

import traceback

import data
import log
import pub
import timecheck


class pv():
    """
    """

    def __init__(self):
        self.data = {}

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
            # Initialer Aufruf
            if "set" not in self.data:
                self.data["set"] = {}
            if len(data.pv_data) > 1:
                self.data["config"]["configured"]=True
                if "pv_available_prev" not in self.data["set"]:
                    self.data["set"]["pv_available_prev"] = False
                if "available_power" not in self.data["set"]:
                    self.data["set"]["available_power"] = 0
                if "pv_power_left" not in self.data["get"]:
                    self.data["get"]["pv_power_left"] = 0
                # aktuelle Leistung an der EVU, enthält die Leistung der Einspeisungsgrenze
                used_power = self.data["set"]["available_power"] - self.data["get"]["pv_power_left"]
                evu_power = (
                    data.counter_data["evu"].data["get"]["power_all"] * (-1))
                remaining_power = used_power + evu_power
                # Einspeisungsgrenze (Verschiebung des Regelpunkts)
                if self.data["config"]["feed_in_yield_active"] == True:
                    remaining_power = remaining_power - \
                        self.data["config"]["feed_in_yield"]
                # Regelmodus
                control_range_low = self.data["config"]["control_range"][0]
                control_range_high = self.data["config"]["control_range"][1]
                if control_range_low < evu_power < control_range_high:
                    available_power = used_power
                else:
                    available_power = remaining_power - \
                        ((control_range_high - control_range_low) /
                        2)  # Mitte des Regelbereichs

                self.data["set"]["available_power"] = available_power # normalisierte verfügbare Leistung, Regelpunkt ist bei 0
                log.message_debug_log("debug", str(available_power)+"W PV-Leistung, die für die Regelung verfügbar ist")
            # nur allgemeiner PV-Key vorhanden, d.h. kein Modul konfiguriert
            else:
                self.data["config"]["configured"]=False
                available_power = 0 # normalisierte verfügbare Leistung, Regelpunkt ist bei 0
                log.message_debug_log("debug", "Kein PV-Modul konfiguriert.")
            self.data["set"]["available_power"] = available_power
            pub.pub("openWB/pv/set/available_power", available_power)
            pub.pub("openWB/pv/config/configured", self.data["config"]["configured"])

        except Exception as e:
            log.exception_logging(e)


class pvModule():
    """
    """

    def __init__(self):
        self.data = {}
    """
    """
