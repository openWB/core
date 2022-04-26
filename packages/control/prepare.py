""" Aufbereitung der Daten für den Algorithmus
"""

import copy
import logging

from control import chargelog
from control import data
from helpermodules.pub import Pub
from helpermodules import subdata
from control.bat import Bat
from control.counter import Counter

from control.chargepoint import Chargepoint
from control.pv import Pv

log = logging.getLogger(__name__)


class Prepare:
    def __init__(self):
        pass

    def setup_algorithm(self):
        """ bereitet die Daten für den Algorithmus vor und startet diesen.
        """
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
            # Workaround, da mit Python3.9/pymodbus2.5 eine pymodbus-Instanz nicht mehr kopiert werden kann.
            # Bei einer Neukonfiguration eines Device/Komponente wird dieses Neuinitialisiert. Nur bei Komponenten
            # mit simcount werden Werte aktualisiert, diese sollten jedoch nur einmal nach dem Auslesen aktualisiert
            # werden, sodass die Nutzung einer Referenz vorerst funktioniert.
            data.data.system_data = {
                "system": copy.deepcopy(subdata.SubData.system_data["system"])} | {
                k: subdata.SubData.system_data[k] for k in subdata.SubData.system_data if "device" in k}
        except Exception:
            log.exception("Fehler im Prepare-Modul")

    def __copy_counter_data(self):
        data.data.counter_data.clear()
        for counter in subdata.SubData.counter_data:
            stop = False
            if isinstance(subdata.SubData.counter_data[counter], Counter):
                for dev in subdata.SubData.system_data:
                    if "device" in dev:
                        for component in subdata.SubData.system_data[dev].components:
                            if component[9:] == counter[7:]:
                                data.data.counter_data[counter] = copy.deepcopy(subdata.SubData.counter_data[counter])
                                stop = True
                                break
                    if stop:
                        break
            else:
                data.data.counter_data[counter] = copy.deepcopy(subdata.SubData.counter_data[counter])

    def copy_module_data(self):
        """ kopiert die Daten, die per MQTT empfangen wurden.
        """
        try:
            self.__copy_counter_data()
            data.data.pv_data.clear()
            for pv in subdata.SubData.pv_data:
                stop = False
                if isinstance(subdata.SubData.pv_data[pv], Pv):
                    for dev in subdata.SubData.system_data:
                        if "device" in dev:
                            for component in subdata.SubData.system_data[dev].components:
                                if component[9:] == pv[2:]:
                                    data.data.pv_data[pv] = copy.deepcopy(subdata.SubData.pv_data[pv])
                                    stop = True
                                    break
                        if stop:
                            break
                else:
                    data.data.pv_data[pv] = copy.deepcopy(subdata.SubData.pv_data[pv])
            data.data.bat_data.clear()
            for bat in subdata.SubData.bat_data:
                stop = False
                if isinstance(subdata.SubData.bat_data[bat], Bat):
                    for dev in subdata.SubData.system_data:
                        if "device" in dev:
                            for component in subdata.SubData.system_data[dev].components:
                                if component[9:] == bat[3:]:
                                    data.data.bat_data[bat] = copy.deepcopy(subdata.SubData.bat_data[bat])
                                    stop = True
                                    break
                        if stop:
                            break
                else:
                    data.data.bat_data[bat] = copy.deepcopy(subdata.SubData.bat_data[bat])
        except Exception:
            log.exception("Fehler im Prepare-Modul")

    def copy_data(self):
        """ kopiert die Daten, die per MQTT empfangen wurden.
        """
        try:
            data.data.general_data = copy.deepcopy(subdata.SubData.general_data)
            data.data.optional_data = copy.deepcopy(subdata.SubData.optional_data)
            data.data.cp_data.clear()
            for cp in subdata.SubData.cp_data:
                if isinstance(subdata.SubData.cp_data[cp], Chargepoint):
                    if "config" in subdata.SubData.cp_data[cp].data:
                        data.data.cp_data[cp] = copy.deepcopy(subdata.SubData.cp_data[cp])
                else:
                    data.data.cp_data[cp] = copy.deepcopy(subdata.SubData.cp_data[cp])
            data.data.cp_template_data = copy.deepcopy(subdata.SubData.cp_template_data)
            for chargepoint in data.data.cp_data:
                try:
                    if "cp" in chargepoint:
                        data.data.cp_data[chargepoint].template = data.data.cp_template_data["cpt" + str(
                            data.data.cp_data[chargepoint].data["config"]["template"])]
                        # Status zurücksetzen (wird jeden Zyklus neu ermittelt)
                        data.data.cp_data[chargepoint].data["get"]["state_str"] = None
                except Exception:
                    log.exception("Fehler im Prepare-Modul für Ladepunkt "+str(chargepoint))
            data.data.ev_data.clear()
            for ev in subdata.SubData.ev_data:
                if "name" in subdata.SubData.ev_data[ev].data:
                    data.data.ev_data[ev] = copy.deepcopy(subdata.SubData.ev_data[ev])
            data.data.ev_template_data = copy.deepcopy(subdata.SubData.ev_template_data)
            data.data.ev_charge_template_data = copy.deepcopy(subdata.SubData.ev_charge_template_data)
            for vehicle in data.data.ev_data:
                try:
                    # Globaler oder individueller Lademodus?
                    if data.data.general_data["general"].data["chargemode_config"]["individual_mode"]:
                        data.data.ev_data[vehicle].charge_template = data.data.ev_charge_template_data["ct" + str(
                            data.data.ev_data[vehicle].data["charge_template"])]
                    else:
                        data.data.ev_data[vehicle].charge_template = data.data.ev_charge_template_data["ct0"]
                    # zuerst das aktuelle Template laden
                    data.data.ev_data[vehicle].ev_template = data.data.ev_template_data["et" + str(
                        data.data.ev_data[vehicle].data["ev_template"])]
                except Exception:
                    log.exception("Fehler im Prepare-Modul für EV "+str(vehicle))

            self.__copy_counter_data()
            data.data.graph_data = copy.deepcopy(subdata.SubData.graph_data)
        except Exception:
            log.exception("Fehler im Prepare-Modul")

    def _check_chargepoints(self):
        """ ermittelt die gewünschte Stromstärke für jeden LP.
        """
        data.data.cp_data["all"].get_cp_sum()
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
                            Pub().pub("openWB/set/chargepoint/" +
                                      str(cp.cp_num)+"/set/charging_ev", vehicle)
                            charging_ev.ev_template.data = charging_ev.data["set"]["ev_template"]
                            cp.data["set"]["charging_ev_data"] = charging_ev
                            Pub().pub("openWB/set/chargepoint/"+str(cp.cp_num) +
                                      "/set/change_ev_permitted", [True, ""])
                        else:
                            # Darf das EV geändert werden?
                            if (cp.data["set"]["log"]["imported_at_plugtime"] == 0 or
                                    cp.data["set"]["log"]["imported_at_plugtime"] == cp.data["get"]["imported"]):
                                cp.data["set"]["charging_ev"] = vehicle
                                Pub().pub("openWB/set/chargepoint/" +
                                          str(cp.cp_num)+"/set/charging_ev", vehicle)
                                cp.data["set"]["charging_ev_data"] = charging_ev
                                Pub().pub("openWB/set/chargepoint/"+str(cp.cp_num) +
                                          "/set/change_ev_permitted", [True, ""])
                                charging_ev.data["set"]["ev_template"] = charging_ev.ev_template.data
                                Pub().pub("openWB/set/vehicle/"+str(charging_ev.ev_num) +
                                          "/set/ev_template", charging_ev.data["set"]["ev_template"])
                            else:
                                # Altes EV beibehalten.
                                if cp.data["set"]["charging_ev"] != -1:
                                    vehicle = cp.data["set"]["charging_ev"]
                                elif cp.data["set"]["charging_ev_prev"] != -1:
                                    vehicle = cp.data["set"]["charging_ev_prev"]
                                    cp.data["set"]["charging_ev"] = vehicle
                                    Pub().pub(
                                        "openWB/set/chargepoint/"+str(cp.cp_num)+"/set/charging_ev", vehicle)
                                    cp.data["set"]["charging_ev_prev"] = -1
                                    Pub().pub(
                                        "openWB/set/chargepoint/"+str(cp.cp_num)+"/set/charging_ev_prev", -1)
                                else:
                                    raise ValueError(
                                        "Wenn kein aktuelles und kein vorheriges Ev zugeordnet waren, \
                                            sollte noch nicht geladen worden sein.")
                                charging_ev = data.data.ev_data["ev" + str(vehicle)]
                                charging_ev.ev_template.data = charging_ev.data["set"]["ev_template"]
                                cp.data["set"]["charging_ev_data"] = charging_ev
                                Pub().pub("openWB/set/chargepoint/"+str(cp.cp_num)+"/set/change_ev_permitted", [
                                    False, "Das Fahrzeug darf nur geändert werden, wenn noch nicht geladen wurde. \
                                            Bitte abstecken, dann wird das gewählte Fahrzeug verwendet."])
                                log.warning(
                                    "Das Fahrzeug darf nur geändert werden, wenn noch nicht geladen wurde.")

                        phases = cp.get_phases(
                            charging_ev.charge_template.data["chargemode"]["selected"])
                        state, message_ev, submode, required_current = charging_ev.get_required_current(
                            cp.data["set"]["log"]["imported_since_mode_switch"])
                        self._pub_connected_vehicle(charging_ev, cp)
                        # Einhaltung des Minimal- und Maximalstroms prüfen
                        required_current = charging_ev.check_min_max_current(
                            required_current, charging_ev.data["control_parameter"]["phases"])
                        current_changed, mode_changed = charging_ev.check_state(
                            required_current, cp.data["set"]["current"], cp.data["get"]["charge_state"])

                        if message_ev is not None:
                            message = message_ev

                        # Die benötigte Stromstärke hat sich durch eine Änderung des Lademodus oder der Konfiguration
                        # geändert. Die Zuteilung entsprechend der Priorisierung muss neu geprüft werden. Daher muss
                        # der LP zurückgesetzt werden, wenn er gerade lädt, um in der Regelung wieder berücksichtigt
                        # zu werden.
                        if current_changed:
                            log.debug(f"LP{cp.cp_num}: Da sich die Stromstärke geändert hat, muss der Ladepunkt im "
                                      "Algorithmus neu priorisiert werden.")
                            data.data.pv_data["all"].reset_switch_on_off(
                                cp, charging_ev)
                            charging_ev.reset_phase_switch()
                            min_charge_current = cp.data["set"]["current"] - \
                                charging_ev.ev_template.data["nominal_difference"]
                            if max(cp.data["get"]["currents"]) > min_charge_current:
                                cp.data["set"]["current"] = 0
                            else:
                                # Wenn nicht geladen wird, obwohl geladen werde kann, soll das EV im Algorithmus nicht
                                # berücksichtigt werden. Wenn der Sollstrom gesetzt ist, wird das EV nur im LM
                                # berücksichtigt.
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
                        if not state:
                            if cp.data["set"]["charging_ev"] != -1:
                                # Altes EV merken
                                cp.data["set"]["charging_ev_prev"] = cp.data["set"]["charging_ev"]
                                Pub().pub("openWB/set/chargepoint/"+str(cp.cp_num) +
                                          "/set/charging_ev_prev", cp.data["set"]["charging_ev_prev"])
                            cp.data["set"]["charging_ev"] = -1
                            Pub().pub("openWB/set/chargepoint/" +
                                      str(cp.cp_num)+"/set/charging_ev", -1)
                            log.debug(
                                "LP " + str(cp.cp_num) + ", EV: " + cp.data["set"]["charging_ev_data"].data["name"] +
                                " (EV-Nr." + str(vehicle) + "): Lademodus " +
                                str(charging_ev.charge_template.data["chargemode"]["selected"]) + ", Submodus: " +
                                str(charging_ev.data["control_parameter"]["submode"]))
                        else:
                            if (charging_ev.data["control_parameter"]["timestamp_switch_on_off"] is not None and
                                    not cp.data["get"]["charge_state"] and
                                    data.data.pv_data["all"].data["set"]["overhang_power_left"] == 0):
                                log.error("Reservierte Leistung kann nicht 0 sein.")

                            log.debug(
                                "LP " + str(cp.cp_num) + ", EV: " + cp.data["set"]["charging_ev_data"].data
                                ["name"] + " (EV-Nr." + str(vehicle) + "): Theoretisch benötigter Strom " +
                                str(required_current) + "A, Lademodus " +
                                str(charging_ev.charge_template.data["chargemode"]["selected"]) + ", Submodus: " +
                                str(charging_ev.data["control_parameter"]["submode"]) + ", Phasen: " + str(phases) +
                                ", Priorität: " + str(charging_ev.charge_template.data["prio"]) +
                                ", max. Ist-Strom: " + str(max(cp.data["get"]["currents"])))
                    else:
                        # Wenn kein EV zur Ladung zugeordnet wird, auf hinterlegtes EV zurückgreifen.
                        self._pub_connected_vehicle(
                            data.data.ev_data["ev"+str(cp.data["config"]["ev"])], cp)
                    if message is not None and cp.data["get"]["state_str"] is None:
                        log.info("LP "+str(cp.cp_num)+": "+message)
                        cp.data["get"]["state_str"] = message
            except Exception:
                log.exception("Fehler im Prepare-Modul für Ladepunkt "+str(cp_item))
        data.data.cp_data["all"].no_charge()

    def _pub_connected_vehicle(self, vehicle, chargepoint):
        """ published die Daten, die zur Anzeige auf der Hauptseite benötigt werden.

        Parameter
        ---------
        vehicle: dict
            EV, das dem LP zugeordnet ist
        cp_num: int
            LP-Nummer
        """
        try:
            soc_config_obj = {
                # "configured": vehicle.data["soc"]["config"]["configured"],
                # "manual": vehicle.data["soc"]["config"]["manual"]
            }
            soc_obj = {
                "range_charged": chargepoint.data["set"]["log"]["range_charged"],
                "range_unit": data.data.general_data["general"].data["range_unit"],
            }
            if vehicle.data["get"].get("soc_timestamp"):
                soc_obj.update({"timestamp": vehicle.data["get"]["soc_timestamp"],
                                "soc": vehicle.data["get"]["soc"],
                                "fault_state": vehicle.data["get"]["fault_state"],
                                "fault_str": vehicle.data["get"]["fault_str"]})
            if vehicle.data["get"].get("range"):
                soc_obj.update({"range": vehicle.data["get"]["range"]})
            info_obj = {"id": vehicle.ev_num,
                        "name": vehicle.data["name"]}
            if (vehicle.charge_template.data["chargemode"]["selected"] == "time_charging" or
                    vehicle.charge_template.data["chargemode"]["selected"] == "scheduled_charging"):
                current_plan = vehicle.data["control_parameter"]["current_plan"]
            else:
                current_plan = None
            config_obj = {"charge_template": vehicle.charge_template.ct_num,
                          "ev_template": vehicle.ev_template.et_num,
                          "chargemode": vehicle.charge_template.data["chargemode"]["selected"],
                          "priority": vehicle.charge_template.data["prio"],
                          "current_plan": current_plan,
                          "average_consumption": vehicle.ev_template.data["average_consump"]}
            if soc_config_obj != chargepoint.data["get"]["connected_vehicle"]["soc_config"]:
                Pub().pub("openWB/chargepoint/"+str(chargepoint.cp_num) +
                          "/get/connected_vehicle/soc_config", soc_config_obj)
            if soc_obj != chargepoint.data["get"]["connected_vehicle"]["soc"]:
                Pub().pub("openWB/chargepoint/"+str(chargepoint.cp_num) +
                          "/get/connected_vehicle/soc", soc_obj)
            if info_obj != chargepoint.data["get"]["connected_vehicle"]["info"]:
                Pub().pub("openWB/chargepoint/"+str(chargepoint.cp_num) +
                          "/get/connected_vehicle/info", info_obj)
            if config_obj != chargepoint.data["get"]["connected_vehicle"]["config"]:
                Pub().pub("openWB/chargepoint/"+str(chargepoint.cp_num) +
                          "/get/connected_vehicle/config", config_obj)
        except Exception:
            log.exception("Fehler im Prepare-Modul")

    def _use_pv(self):
        """ ermittelt, ob Überschuss an der EVU vorhanden ist.
        """
        try:
            data.data.pv_data["all"].calc_power_for_control()
        except Exception:
            log.exception("Fehler im Prepare-Modul")

    def _bat(self):
        """ ermittelt, ob Überschuss am Speicher verfügbar ist.
        """
        try:
            data.data.bat_data["all"].setup_bat()
        except Exception:
            log.exception("Fehler im Prepare-Modul")

    def _counter(self):
        """ initialisiert alle Zähler für den Algorithmus
        """
        try:
            for counter in data.data.counter_data:
                if "counter" in counter:
                    data.data.counter_data[counter].setup_counter()
        except Exception:
            log.exception("Fehler im Prepare-Modul")

    def _get_home_consumption(self):
        """ ermittelt den Hausverbrauch.
        """
        try:
            data.data.counter_data["all"].calc_home_consumption()
        except Exception:
            log.exception("Fehler im Prepare-Modul")
