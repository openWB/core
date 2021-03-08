""" Aufbereitung der Daten für den Algorithmus
"""

import copy
import traceback

import algorithm
import bat
import data
import log
import pub
import stats
import subdata


class prepare():
    """ 
    """

    def __init__(self):
        self.control = algorithm.control()

    def setup_algorithm(self):
        """ bereitet die Daten für den Algorithmus vor und startet diesen.
        """
        self._copy_data()
        self._check_chargepoints()
        self._use_pv()
        self._bat()
        self.control.calc_current()

    def _copy_data(self):
        """ kopiert die Daten, die per MQTT empfangen wurden.
        """
        try:
            data.cp_data = copy.deepcopy(subdata.subData.cp_data)
            data.cp_template_data = copy.deepcopy(
                subdata.subData.cp_template_data)
            for chargepoint in data.cp_data:
                if "cp" in chargepoint:
                    data.cp_data[chargepoint].template = data.cp_template_data["cpt" +
                                                                               str(data.cp_data[chargepoint].data["config"]["template"])]
                    data.cp_data[chargepoint].cp_num = chargepoint[2:]

            data.pv_data = copy.deepcopy(subdata.subData.pv_data)
            data.ev_data = copy.deepcopy(subdata.subData.ev_data)
            data.ev_template_data = copy.deepcopy(
                subdata.subData.ev_template_data)
            data.ev_charge_template_data = copy.deepcopy(
                subdata.subData.ev_charge_template_data)
            for vehicle in data.ev_data:
                data.ev_data[vehicle].charge_template = data.ev_charge_template_data["ct" +
                                                                                     str(data.ev_data[vehicle].data["charge_template"])]
                data.ev_data[vehicle].ev_template = data.ev_template_data["et" +
                                                                          str(data.ev_data[vehicle].data["ev_template"])]
                data.ev_data[vehicle].ev_num = vehicle[2:]

            data.counter_data = copy.deepcopy(subdata.subData.counter_data)
            data.bat_module_data = copy.deepcopy(
                subdata.subData.bat_module_data)
            data.general_data = copy.deepcopy(subdata.subData.general_data)
            data.optional_data = copy.deepcopy(subdata.subData.optional_data)
            data.graph_data = copy.deepcopy(subdata.subData.graph_data)

            data.print_all()
        except KeyError as key:
            print("dictionary key", key, "doesn't exist in _copy_data")

    def _check_chargepoints(self):
        """ ermittelt die gewünschte Stromstärke für jeden LP.
        """
        for chargepoint in data.cp_data:
            try:
                if "cp" in chargepoint:
                    vehicle = data.cp_data[chargepoint].get_state()
                    if "set" not in data.cp_data[chargepoint].data:
                        data.cp_data[chargepoint].data["set"] = {}
                    if vehicle != None:
                        if vehicle == 0:
                            data.cp_data[chargepoint].data["set"]["charging_ev"] = data.ev_data["default"]
                            data.ev_data["default"].get_required_current()
                        else:
                            data.cp_data[chargepoint].data["set"]["charging_ev"] = data.ev_data["ev"+str(
                                vehicle)]
                            data.ev_data["ev"+str(vehicle)].get_required_current()
                        log.message_debug_log("debug", "Ladepunkt "+data.cp_data[chargepoint].cp_num+",: EV "+data.cp_data[chargepoint].data["set"]["charging_ev"].data["name"]+" (EV-Nr."+str(vehicle)+")")
                    else:
                        if "charging_ev" in data.cp_data[chargepoint].data:
                            data.cp_data[chargepoint].data["set"].pop("charging_ev")
            except:
                traceback.print_exc(limit=-1)

    def _use_pv(self):
        """ ermittelt, ob Überschuss an der EVU vorhanden ist und kümmert sich um die Beachtung der Einspeisungsgrenze.
        """
        data.pv_data["pv"].calc_power_for_control()

    def _bat(self):
        if data.bat_module_data: 
            data.bat_module_data["bat"] = bat.bat()
            data.bat_module_data["bat"].setup_bat()