""" Aufbereitung der Daten für den Algorithmus
"""

import copy

from . import chargelog
from . import chargepoint
from . import data
from ..helpermodules import log
from ..helpermodules import pub
from ..helpermodules import subdata


class prepare:
    """ 
    """

    def __init__(self):
        pass

    def setup_algorithm(self):
        """ bereitet die Daten für den Algorithmus vor und startet diesen.
        """
        log.MainLogger().info("# ***Start*** ")
        self._counter()
        self._check_chargepoints()
        self._use_pv()
        self._bat()
        self._get_home_consumption()
        data.data.print_all()

    def copy_system_data(self):
        """ kopiert die Daten, die per MQTT empfangen wurden.
        """
        try:
            data.data.system_data = copy.deepcopy(subdata.SubData.system_data)
        except Exception:
            log.MainLogger().exception("Fehler im Prepare-Modul")

    def copy_counter_data(self):
        """ kopiert die Daten, die per MQTT empfangen wurden.
        """
        try:
            data.data.counter_data = copy.deepcopy(
                subdata.SubData.counter_data)
        except Exception:
            log.MainLogger().exception("Fehler im Prepare-Modul")

    def copy_data(self):
        """ kopiert die Daten, die per MQTT empfangen wurden.
        """
        try:
            data.data.general_data = copy.deepcopy(
                subdata.SubData.general_data)
            data.data.optional_data = copy.deepcopy(
                subdata.SubData.optional_data)
            data.data.cp_data = copy.deepcopy(subdata.SubData.cp_data)
            data.data.cp_template_data = copy.deepcopy(
                subdata.SubData.cp_template_data)
            for chargepoint in data.data.cp_data:
                try:
                    if "cp" in chargepoint:
                        data.data.cp_data[chargepoint].template = data.data.cp_template_data["cpt" + str(
                            data.data.cp_data[chargepoint].data["config"]["template"])]
                        # Status zurücksetzen (wird jeden Zyklus neu ermittelt)
                        data.data.cp_data[chargepoint].data["get"]["state_str"] = None
                except Exception:
                    log.MainLogger().exception("Fehler im Prepare-Modul fuer Ladepunkt "+str(chargepoint))

            data.data.pv_data = copy.deepcopy(subdata.SubData.pv_data)
            data.data.pv_module_data = copy.deepcopy(
                subdata.SubData.pv_module_data)
            data.data.ev_data = copy.deepcopy(subdata.SubData.ev_data)
            data.data.ev_template_data = copy.deepcopy(
                subdata.SubData.ev_template_data)
            data.data.ev_charge_template_data = copy.deepcopy(
                subdata.SubData.ev_charge_template_data)
            for vehicle in data.data.ev_data:
                try:
                    # Globaler oder individueller Lademodus?
                    if data.data.general_data["general"].data["chargemode_config"]["individual_mode"]:
                        data.data.ev_data[vehicle].charge_template = data.data.ev_charge_template_data["ct" + str(
                            data.data.ev_data[vehicle].data["charge_template"])]
                    else:
                        data.data.ev_data[vehicle].charge_template = data.data.ev_charge_template_data["ct0"]
                    # erstmal das aktuelle Template laden
                    data.data.ev_data[vehicle].ev_template = data.data.ev_template_data["et" + str(
                        data.data.ev_data[vehicle].data["ev_template"])]
                except Exception:
                    log.MainLogger().exception("Fehler im Prepare-Modul fuer EV "+str(vehicle))

            data.data.counter_data = copy.deepcopy(
                subdata.SubData.counter_data)
            data.data.bat_data = copy.deepcopy(subdata.SubData.bat_data)
            data.data.bat_module_data = copy.deepcopy(
                subdata.SubData.bat_module_data)
        except Exception:
            log.MainLogger().exception("Fehler im Prepare-Modul")

    def _check_chargepoints(self):
        """ ermittelt die gewünschte Stromstärke für jeden LP.
        """
        data.data.cp_data["all"].get_power_counter_all()
        data.data.cp_data["all"].match_rfid_to_cp()
        for cp_item in data.data.cp_data:
            state = True
            try:
                if "cp" in cp_item:
                    cp = data.data.cp_data[cp_item]
                    vehicle, message = cp.get_state()
                    if vehicle != -1:
                        charging_ev = data.data.ev_data["ev"+str(vehicle)]
                        # Das EV darf nur gewechselt werden, wenn noch nicht geladen wurde.
                        if (cp.data["set"]["charging_ev"] == vehicle or
                                cp.data["set"]["charging_ev_prev"] == vehicle):
                            # Das EV entspricht dem bisherigen EV.
                            cp.data["set"]["charging_ev"] = vehicle
                            pub.pub("openWB/set/chargepoint/" +
                                    str(cp.cp_num)+"/set/charging_ev", vehicle)
                            charging_ev.ev_template.data = charging_ev.data["set"]["ev_template"]
                            cp.data["set"]["charging_ev_data"] = charging_ev
                            pub.pub("openWB/set/chargepoint/"+str(cp.cp_num) +
                                    "/set/change_ev_permitted", [True, ""])
                        else:
                            # Darf das EV geändert werden?
                            if (cp.data["set"]["log"]["counter_at_plugtime"] == 0 or
                                    cp.data["set"]["log"]["counter_at_plugtime"] == cp.data["get"]["counter"]):
                                cp.data["set"]["charging_ev"] = vehicle
                                pub.pub("openWB/set/chargepoint/" +
                                        str(cp.cp_num)+"/set/charging_ev", vehicle)
                                cp.data["set"]["charging_ev_data"] = charging_ev
                                pub.pub("openWB/set/chargepoint/"+str(cp.cp_num) +
                                        "/set/change_ev_permitted", [True, ""])
                                charging_ev.data["set"]["ev_template"] = charging_ev.ev_template.data
                                pub.pub("openWB/set/vehicle/"+str(charging_ev.ev_num) +
                                        "/set/ev_template", charging_ev.data["set"]["ev_template"])
                            else:
                                # Altes EV beibehalten.
                                if cp.data["set"]["charging_ev"] != -1:
                                    vehicle = cp.data["set"]["charging_ev"]
                                elif cp.data["set"]["charging_ev_prev"] != -1:
                                    vehicle = cp.data["set"]["charging_ev_prev"]
                                    cp.data["set"]["charging_ev"] = vehicle
                                    pub.pub(
                                        "openWB/set/chargepoint/"+str(cp.cp_num)+"/set/charging_ev", vehicle)
                                    cp.data["set"]["charging_ev_prev"] = -1
                                    pub.pub(
                                        "openWB/set/chargepoint/"+str(cp.cp_num)+"/set/charging_ev_prev", -1)
                                else:
                                    raise ValueError(
                                        "Wenn kein aktuelles und kein vorheriges Ev zugeordnet waren, \
                                            sollte noch nicht geladen worden sein.")
                                charging_ev = data.data.ev_data["ev" +
                                                                str(vehicle)]
                                charging_ev.ev_template.data = charging_ev.data["set"]["ev_template"]
                                cp.data["set"]["charging_ev_data"] = charging_ev
                                pub.pub("openWB/set/chargepoint/"+str(cp.cp_num)+"/set/change_ev_permitted", [
                                        False, "Das Fahrzeug darf nur geändert werden, wenn noch nicht geladen wurde. \
                                            Bitte abstecken, dann wird das gewählte Fahrzeug verwendet."])
                                log.MainLogger().warning(
                                    "Das Fahrzeug darf nur geändert werden, wenn noch nicht geladen wurde.")

                        phases = cp.get_phases(
                            charging_ev.charge_template.data["chargemode"]["selected"])
                        state, message_ev, submode, required_current = charging_ev.get_required_current(
                            cp.data["set"]["log"]["charged_since_mode_switch"])
                        self._pub_connected_vehicle(charging_ev, cp)
                        # Einhaltung des Minimal- und Maximalstroms prüfen
                        required_current = charging_ev.check_min_max_current(
                            required_current, charging_ev.data["control_parameter"]["phases"])
                        current_changed, mode_changed = charging_ev.check_state(
                            required_current, cp.data["set"]["current"], cp.data["get"]["charge_state"])

                        if message_ev is not None:
                            message = message_ev
                        log.MainLogger().debug("Ladepunkt "+str(cp.cp_num)+", EV: " +
                                               cp.data["set"]["charging_ev_data"].data["name"]+" (EV-Nr."+str(vehicle)+")")

                        # Die benötigte Stromstärke hat sich durch eine Änderung des Lademdous oder der Konfiguration
                        # geändert. Die Zuteilung entsprechend der Priorisierung muss neu geprüft werden. Daher muss
                        # der LP zurückgesetzt werden, wenn er gerade lädt, um in der Regelung wieder berücksichtigt
                        # zu werden.
                        if current_changed:
                            log.MainLogger().debug("LP"+str(cp.cp_num) +
                                                   " : Da sich die Stromstärke geändert hat, muss der Ladepunkt im \
                                                       Algorithmus neu priorisiert werden.")
                            data.data.pv_data["all"].reset_switch_on_off(
                                cp, charging_ev)
                            charging_ev.reset_phase_switch()
                            if max(cp.data["get"]["current"]) > charging_ev.ev_template.data["nominal_difference"]:
                                cp.data["set"]["current"] = 0
                            else:
                                # Wenn nicht geladen wird, obwohl geladen werde kann, soll das EV im Algorithmus nicht
                                # berücksichtigt werden.
                                cp.data["set"]["current"] = required_current
                            # Da nicht bekannt ist, ob mit Bezug, Überschuss oder aus dem Speicher geladen wird, wird
                            # die freiwerdende Leistung erst im nächsten Durchlauf berücksichtigt. Ggf. entsteht so
                            # eine kurze Unterbrechung der Ladung, wenn während dem Laden umkonfiguriert wird.
                        charging_ev.set_control_parameter(
                            submode, required_current)
                        # Ein Eintrag muss nur erstellt werden, wenn vorher schon geladen wurde und auch danach noch
                        # geladen werden soll.
                        if mode_changed and cp.data["get"]["charge_state"] and state:
                            chargelog.save_data(cp, charging_ev)

                        # Wenn die Nachrichten gesendet wurden, EV wieder löschen, wenn das EV im Algorithmus nicht
                        # berücksichtigt werden soll.
                        if state is False:
                            if cp.data["set"]["charging_ev"] != -1:
                                # Altes EV merken
                                cp.data["set"]["charging_ev_prev"] = cp.data["set"]["charging_ev"]
                                pub.pub("openWB/set/chargepoint/"+str(cp.cp_num) +
                                        "/set/charging_ev_prev", cp.data["set"]["charging_ev_prev"])
                            cp.data["set"]["charging_ev"] = -1
                            pub.pub("openWB/set/chargepoint/" +
                                    str(cp.cp_num)+"/set/charging_ev", -1)
                            log.MainLogger().debug("EV"+str(charging_ev.ev_num)+": Lademodus " +
                                                   str(charging_ev.charge_template.data["chargemode"]["selected"]) +
                                                   ", Submodus: " +
                                                   str(charging_ev.data["control_parameter"]["submode"]))
                        else:
                            if (charging_ev.data["control_parameter"]["timestamp_switch_on_off"] != "0" and
                                    cp.data["get"]["charge_state"] is False and
                                    data.data.pv_data["all"].data["set"]["overhang_power_left"] == 0):
                                log.MainLogger().error("Reservierte Leistung kann nicht 0 sein.")

                            log.MainLogger().debug(
                                "EV" + str(charging_ev.ev_num) + ": Theroretisch benötigter Strom " +
                                str(required_current) + "A, Lademodus " +
                                str(charging_ev.charge_template.data["chargemode"]["selected"]) + ", Submodus: " +
                                str(charging_ev.data["control_parameter"]["submode"]) + ", Phasen: " + str(phases) +
                                ", Prioritaet: " + str(charging_ev.charge_template.data["prio"]) + ", max. Ist-Strom: " +
                                str(max(cp.data["get"]["current"])))
                    else:
                        # Wenn kein EV zur Ladung zugeordnet wird, auf hinterlegtes EV zurückgreifen.
                        self._pub_connected_vehicle(
                            data.data.ev_data["ev"+str(cp.data["config"]["ev"])], cp)
                    if message is not None and cp.data["get"]["state_str"] is None:
                        log.MainLogger().info("LP "+str(cp.cp_num)+": "+message)
                        cp.data["get"]["state_str"] = message
            except Exception:
                log.MainLogger().exception("Fehler im Prepare-Modul fuer Ladepunkt "+str(cp_item))
        if "all" not in data.data.cp_data:
            data.data.cp_data["all"] = chargepoint.allChargepoints()
        data.data.cp_data["all"].no_charge()

    def _pub_connected_vehicle(self, vehicle, chargepoint):
        """ published die Daten, die zur Anzeige auf der Haupseite benötigt werden.

        Parameter
        ---------
        vehicle: dict
            EV, das dem LP zugeordnet ist
        cp_num: int
            LP-Nummer
        """
        try:
            soc_config_obj = {"configured": vehicle.data["soc"]["config"]["configured"],
                              "manual": vehicle.data["soc"]["config"]["manual"]}
            soc_obj = {"soc": vehicle.data["get"]["soc"],
                       "range": chargepoint.data["set"]["log"]["range_charged"],
                       "range_unit": data.data.general_data["general"].data["range_unit"],
                       "timestamp": vehicle.data["get"]["soc_timestamp"],
                       "fault_stat": vehicle.data["soc"]["get"]["fault_state"],
                       "fault_str": vehicle.data["soc"]["get"]["fault_str"]}
            info_obj = {"id": vehicle.ev_num,
                        "name": vehicle.data["name"]}
            if vehicle.charge_template.data["chargemode"]["selected"] == "time_charging":
                current_plan = vehicle.charge_template.data["chargemode"]["current_plan"]
            elif vehicle.charge_template.data["chargemode"]["selected"] == "scheduled_charging":
                current_plan = vehicle.charge_template.data["chargemode"]["current_plan"]
            else:
                current_plan = ""
            config_obj = {"charge_template": vehicle.charge_template.ct_num,
                          "ev_template": vehicle.ev_template.et_num,
                          "chargemode": vehicle.charge_template.data["chargemode"]["selected"],
                          "priority": vehicle.charge_template.data["prio"],
                          "current_plan": current_plan,
                          "average_consumption": vehicle.ev_template.data["average_consump"]}
            if soc_config_obj != chargepoint.data["get"]["connected_vehicle"]["soc_config"]:
                pub.pub("openWB/chargepoint/"+str(chargepoint.cp_num) +
                        "/get/connected_vehicle/soc_config", soc_config_obj)
            if soc_obj != chargepoint.data["get"]["connected_vehicle"]["soc"]:
                pub.pub("openWB/chargepoint/"+str(chargepoint.cp_num) +
                        "/get/connected_vehicle/soc", soc_obj)
            if info_obj != chargepoint.data["get"]["connected_vehicle"]["info"]:
                pub.pub("openWB/chargepoint/"+str(chargepoint.cp_num) +
                        "/get/connected_vehicle/info", info_obj)
            if config_obj != chargepoint.data["get"]["connected_vehicle"]["config"]:
                pub.pub("openWB/chargepoint/"+str(chargepoint.cp_num) +
                        "/get/connected_vehicle/config", config_obj)
        except Exception:
            log.MainLogger().exception("Fehler im Prepare-Modul")

    def _use_pv(self):
        """ ermittelt, ob Überschuss an der EVU vorhanden ist.
        """
        try:
            data.data.pv_data["all"].calc_power_for_control()
        except Exception:
            log.MainLogger().exception("Fehler im Prepare-Modul")

    def _bat(self):
        """ ermittelt, ob Überschuss am Speicher verfügbar ist.
        """
        try:
            data.data.bat_data["all"].setup_bat()
        except Exception:
            log.MainLogger().exception("Fehler im Prepare-Modul")

    def _counter(self):
        """ initialisiert alle Zähler für den Algorithmus
        """
        try:
            for counter in data.data.counter_data:
                if "counter" in counter:
                    data.data.counter_data[counter].setup_counter()
        except Exception:
            log.MainLogger().exception("Fehler im Prepare-Modul")

    def _get_home_consumption(self):
        """ ermittelt den Hausverbrauch.
        """
        try:
            data.data.counter_data["all"].calc_home_consumption()
        except Exception:
            log.MainLogger().exception("Fehler im Prepare-Modul")
