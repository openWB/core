"""PV-Logik
Die Leistung, die die PV-Module liefern, kann nicht komplett für das Laden und Smarthome verwendet werden. 
Davon ab geht z.B. noch der Hausverbrauch. Für das Laden mit PV kann deshalb nur der Strom verwendet werden, 
der sonst in das Netz eingespeist werden würde. 
"""

import data
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
        phases = 1  # wie bei indiviudeler automatik ermitteln?
        try:
            # Initialer Aufruf
            if "set" not in self.data:
                self.data["set"] = {}
            if "pv_available_prev" not in self.data["set"]:
                self.data["set"]["pv_available_prev"] = False
            # aktuelle Leistung an der EVU, enthält die Leistung der Einspeisungsgrenze
            evu_power = (
                data.counter_data["evu"].data["get"]["power_all"] * (-1))
            remaining_power = self.data["get"]["used_power"] + evu_power
            # Einspeisungsgrenze (Verschiebung des Regelpunkts)
            if self.data["config"]["feed_in_yield_active"] == True:
                remaining_power = remaining_power - \
                    self.data["config"]["feed_in_yield"]
            # Regelmodus
            control_range_low = self.data["config"]["control_range"][0]
            control_range_high = self.data["config"]["control_range"][1]
            if control_range_low < evu_power < control_range_high:
                available_power = self.data["get"]["used_power"]
            else:
                available_power = remaining_power - \
                    ((control_range_high - control_range_low) /
                     2)  # Mitte des Regelbereichs
                if available_power < 0:
                    available_power = 0

            # Ein-/Ausschaltverzögerung
            if self.data["set"]["pv_available_prev"] == False:
                if available_power > self.data["config"]["switch_on_threshold"]*phases:
                    if "timestamp_switch_on_off" in self.data["set"]:
                        if timecheck.check_timestamp(self.data["set"]["timestamp_switch_on_off"], self.data["config"]["switch_on_delay"]) == True:
                            power_set = 0
                        else:
                            self.data["set"]["pv_available_prev"] = True
                            self.data["set"]["timestamp_switch_on_off"] = ""
                            power_set = available_power
                    else:
                        self.data["set"]["timestamp_switch_on_off"] = timecheck.create_timestamp()
                        power_set = 0
                else:
                    power_set = 0
            else:
                if available_power < (self.data["config"]["switch_off_threshold"]*(-1)):
                    if "timestamp_switch_on_off" in self.data["set"]:
                        if timecheck.check_timestamp(self.data["set"]["timestamp_switch_on_off"], self.data["config"]["switch_off_delay"]) == True:
                            power_set = available_power
                        else:
                            self.data["set"]["pv_available_prev"] = False
                            self.data["set"]["timestamp_switch_on_off"] = ""
                            power_set = 0
                    else:
                        self.data["set"]["timestamp_switch_on_off"] = timecheck.create_timestamp()
                        power_set = available_power
                else:
                    power_set = available_power

            self.data["set"]["available_power"] = power_set # normalisierte verfügbare Leistung, Regelpunkt ist bei 0
            pub.pub_dict(self.data["set"], "openWB/pv/set")
        except KeyError as key:
            print("dictionary key", key, "doesn't exist in calc_power_for_control")


class pvModule():
    """
    """

    def __init__(self):
        self.data = {}
    """
    """
