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
        for cp_item in data.cp_data:
            try:
                if "cp" in cp_item:
                    cp = data.cp_data[cp_item]
                    vehicle, message = cp.get_state()
                    if vehicle != -1:
                        charging_ev = data.ev_data["ev"+str(vehicle)]
                        self._pub_connected_vehicle(charging_ev, cp.cp_num)
                        state, message_ev, mode_changed = charging_ev.get_required_current()
                        # Wenn sich das Auto ändert und vorher ein Auto zugeordnet war, Werte des alten Autos zurücksetzen.
                        if cp.data["set"]["charging_ev"] != charging_ev.ev_num and cp.data["set"]["charging_ev"] != -1:
                            data.pv_data["all"].reset_switch_on_off(data.ev_data["ev"+str(cp.data["set"]["charging_ev"])])
                            charging_ev.reset_phase_switch()
                            if max(cp.data["get"]["current"]) != 0:
                                cp.data["set"]["current"] = 0
                        cp.data["set"]["charging_ev"] = charging_ev
                        if message_ev != None:
                            message = "Keine Ladung an LP"+str(cp.cp_num)+", da "+str(message_ev)
                        log.message_debug_log("debug", "Ladepunkt "+cp.cp_num+", EV: "+cp.data["set"]["charging_ev"].data["name"]+" (EV-Nr."+str(vehicle)+")")
                        
                        # Die benötigte Stromstärke hat sich durch eine Änderung des Lademdous oder der Konfiguration geändert. Die Zuteilung entsprechend der Priorisierung muss neu geprüft werden.
                        # Daher muss der LP zurückgesetzt werden, wenn er gerade lädt, um in der Regelung wieder berücksichtigt zu werden.
                        if mode_changed == True:
                            data.pv_data["all"].reset_switch_on_off(cp)
                            charging_ev.reset_phase_switch()
                            if max(cp.data["get"]["current"]) != 0:
                                cp.data["set"]["current"] = 0
                            # Da nicht bekannt ist, ob mit Bezug, Überschuss oder aus dem Speicher geladen wird, wird die freiwerdende Leistung erst im nächsten Durchlauf berücksichtigt.
                            # Ggf. entsteht so eine kurze Unterbrechung der Ladung, wenn während dem Laden umkonfiguriert wird.
                        # Wenn die Nachrichten gesendet wurden, EV wieder löschen, wenn das EV im Algorithmus nicht berücksichtigt werden soll.
                        if state == False:
                            cp.data["set"]["charging_ev"] = -1
                            log.message_debug_log("debug", "EV"+str(charging_ev.ev_num)+": Lademodus "+str(charging_ev.charge_template.data["chargemode"]["selected"])+", Submodus: "+str(charging_ev.data["control_parameter"]["submode"]))
                        else:
                            if (charging_ev.data["control_parameter"]["timestamp_switch_on_off"] != "0" and
                                    cp.data["get"]["charge_state"] == False and 
                                    data.pv_data["all"].data["set"]["overhang_power_left"] == 0):
                                log.message_debug_log("error", "Reservierte Leistung kann nicht 0 sein.")
                            cp.get_phases()
                            # Einhaltung des Minimal- und Maximalstroms prüfen
                            required_current = charging_ev.check_min_max_current(charging_ev.data["control_parameter"]["required_current"], charging_ev.data["control_parameter"]["phases"])
                            log.message_debug_log("debug", "EV"+str(charging_ev.ev_num)+": Theroretisch benötigter Strom "+str(required_current)+"A, Lademodus "+str(
                                charging_ev.charge_template.data["chargemode"]["selected"])+", Submodus: "+str(charging_ev.data["control_parameter"]["submode"])+", Prioritaet: "+str(charging_ev.charge_template.data["prio"]))
                            charging_ev.data["control_parameter"]["required_current"] = required_current
                            pub.pub("openWB/set/vehicle/"+str(charging_ev.ev_num )+"/control_parameter/required_current", required_current)
                    else:
                        cp.data["set"]["charging_ev"] = vehicle
                    pub.pub("openWB/set/chargepoint/"+str(cp.cp_num)+"/get/state_str", message)
                    log.message_debug_log("info", message)
            except Exception as e:
                log.exception_logging(e)
        if "all" not in data.cp_data:
            data.cp_data["all"]=chargepoint.allChargepoints()
        data.cp_data["all"].used_power_all()
        data.cp_data["all"].no_charge()

    def _pub_connected_vehicle(self, vehicle, cp_num):
        """ published die Daten, die zur Anzeige auf der Haupseite benötigt werden.

        Parameter
        ---------
        vehicle: dict
            EV, das dem LP zugeordnet ist
        cp_num: int
            LP-Nummer
        """
        soc_config_obj = {"configured": vehicle.data["soc"]["config"]["configured"], 
                "manual": vehicle.data["soc"]["config"]["manual"]}
        soc_obj = {"soc": vehicle.data["get"]["soc"],
                "range": vehicle.data["get"]["range_charged"],
                "range_unit": data.general_data["general"].data["range_unit"],
                "timestamp": vehicle.data["get"]["soc_timestamp"],
                "fault_stat": vehicle.data["soc"]["get"]["fault_state"],
                "fault_str": vehicle.data["soc"]["get"]["fault_str"]}
        info_obj = {"id": vehicle.ev_num,
                "name": vehicle.data["name"]}
        config_obj = {"charge_template": vehicle.charge_template.ct_num,
                "ev_template": vehicle.ev_template.et_num,
                "chargemode": vehicle.charge_template.data["chargemode"]["selected"],
                "priority": vehicle.charge_template.data["prio"],
                "average_consumption": vehicle.ev_template.data["average_consump"]}

        pub.pub("openWB/chargepoint/"+str(cp_num)+"/get/connected_vehicle/soc_config", soc_config_obj)
        pub.pub("openWB/chargepoint/"+str(cp_num)+"/get/connected_vehicle/soc", soc_obj)
        pub.pub("openWB/chargepoint/"+str(cp_num)+"/get/connected_vehicle/info", info_obj)
        pub.pub("openWB/chargepoint/"+str(cp_num)+"/get/connected_vehicle/config", config_obj)

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