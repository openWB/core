""" Aufbereitung der Daten für den Algorithmus
"""

import copy

import bat
import chargepoint
import counter
import data
import loadmanagement
import log
import pub
import stats
import subdata


class prepare():
    """ 
    """

    def __init__(self):
        pass

    def setup_algorithm(self):
        """ bereitet die Daten für den Algorithmus vor und startet diesen.
        """
        self._copy_data()
        self._counter()
        self._check_chargepoints()
        self._use_pv()
        self._bat()

    def _copy_data(self):
        """ kopiert die Daten, die per MQTT empfangen wurden.
        """
        try:
            data.cp_data = copy.deepcopy(subdata.subData.cp_data)
            data.cp_template_data = copy.deepcopy(
                subdata.subData.cp_template_data)
            for chargepoint in data.cp_data:
                if "cp" in chargepoint:
                    data.cp_data[chargepoint].template = data.cp_template_data["cpt" +str(data.cp_data[chargepoint].data["config"]["template"])]
                    data.cp_data[chargepoint].cp_num = chargepoint[2:]

            data.pv_data = copy.deepcopy(subdata.subData.pv_data)
            data.ev_data = copy.deepcopy(subdata.subData.ev_data)
            data.ev_template_data = copy.deepcopy(
                subdata.subData.ev_template_data)
            data.ev_charge_template_data = copy.deepcopy(
                subdata.subData.ev_charge_template_data)
            for vehicle in data.ev_data:
                data.ev_data[vehicle].charge_template = data.ev_charge_template_data["ct" +str(data.ev_data[vehicle].data["charge_template"])]
                data.ev_data[vehicle].ev_template = data.ev_template_data["et" +str(data.ev_data[vehicle].data["ev_template"])]

            data.counter_data = copy.deepcopy(subdata.subData.counter_data)
            for counter in data.counter_data:
                data.counter_data[counter].counter_num = counter[7:]
            data.bat_module_data = copy.deepcopy(
                subdata.subData.bat_module_data)
            data.general_data = copy.deepcopy(subdata.subData.general_data)
            data.optional_data = copy.deepcopy(subdata.subData.optional_data)
            data.graph_data = copy.deepcopy(subdata.subData.graph_data)
            data.print_all()
        except Exception as e:
            log.exception_logging(e)

    def _check_chargepoints(self):
        """ ermittelt die gewünschte Stromstärke für jeden LP.
        """
        for cp in data.cp_data:
            try:
                if "cp" in cp:
                    chargepoint = data.cp_data[cp]
                    vehicle, message = chargepoint.get_state()
                    if vehicle != -1:
                        state, message_ev, mode_changed = data.ev_data["ev"+str(vehicle)].get_required_current()
                        chargepoint.data["set"]["charging_ev"] = data.ev_data["ev"+str(vehicle)]
                        if message_ev != None:
                            message = "Keine Ladung an LP"+str(chargepoint.cp_num)+", da "+str(message_ev)
                        log.message_debug_log("debug", "Ladepunkt "+chargepoint.cp_num+", EV: "+chargepoint.data["set"]["charging_ev"].data["name"]+" (EV-Nr."+str(vehicle)+")")
                        # Wenn die Nachrichten gesendet wurden, EV wieder löschen, wenn das EV im Algorithmus nicht berücksichtigt werden soll.
                        if state == False:
                            chargepoint.data["set"]["charging_ev"] = -1
                        else:
                            phases_changed = chargepoint.get_phases()
                            # Die benötigte Stromstärke hat sich durch eine Änderung des Lademdous oder der Konfiguration geändert. Die Zuteilung entsprechend der Priorisierung muss neu geprüft werden.
                            # Daher muss der LP zurückgesetzt werden, wenn er gerade lädt, um in der Regelung wieder berücksichtigt zu werden.
                            if (mode_changed == True or phases_changed == True) and max(chargepoint.data["get"]["current"]) != 0:
                                chargepoint.data["set"]["current"] = 0
                                freed_current = (max(chargepoint.data["get"]["current"]) )* -1
                                freed_power = freed_current * 230 * chargepoint.data["get"]["phases_in_use"]
                                # Werte aktualisieren
                                loadmanagement.loadmanagement_for_cp(chargepoint, freed_power, freed_current, chargepoint.data["get"]["phases_in_use"])
                    pub.pub("openWB/set/chargepoint/"+str(chargepoint.cp_num)+"/get/state_str", message)
                    log.message_debug_log("info", message)
            except Exception as e:
                log.exception_logging(e)
        if "all" not in data.cp_data:
            data.cp_data["all"]=chargepoint.allChargepoints()
        data.cp_data["all"].used_power_all()
        data.cp_data["all"].no_charge()

    def _use_pv(self):
        """ ermittelt, ob Überschuss an der EVU vorhanden ist.
        """
        try:
            data.pv_data["all"].calc_power_for_control()
        except Exception as e:
            log.exception_logging(e)

    def _bat(self):
        """ ermittelt, ob Überschuss am Speicher verfügbar ist.
        """
        try:
            if "all" not in data.bat_module_data:
                log.message_debug_log("eror", "Keine allgemeinen Daten für Hausspeicher.")
            data.bat_module_data["all"].setup_bat()
        except Exception as e:
                log.exception_logging(e)

    def _counter(self):
        """ initialisiert alle Zähler für den Algorithmus
        """
        try:
            for counter in data.counter_data:
                if "counter" in counter:
                    data.counter_data[counter].setup_counter()
        except Exception as e:
                log.exception_logging(e)