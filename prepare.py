""" Aufbereitung der Daten für den Algorithmus
"""

import copy

import bat
import chargepoint
import counter
import data
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
        self._check_chargepoints()
        self._use_pv()
        self._bat()
        data.counter_data["counter0"].setup_counter()

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
                    vehicle = data.cp_data[cp].get_state()
                    if "set" not in data.cp_data[cp].data:
                        data.cp_data[cp].data["set"] = {}
                    if "charging_ev" in data.cp_data[cp].data:
                        data.cp_data[cp].data["set"].pop("charging_ev")
                    if vehicle != None:
                        if vehicle == 0:
                            if data.ev_data["default"].get_required_current() == True:
                                data.cp_data[cp].data["set"]["charging_ev"] = data.ev_data["default"]
                                log.message_debug_log("debug", "Ladepunkt "+data.cp_data[cp].cp_num+", EV: "+data.cp_data[cp].data["set"]["charging_ev"].data["name"]+" (EV-Nr."+str(vehicle)+")")
                        else:
                            if data.ev_data["ev"+str(vehicle)].get_required_current() == True:
                                data.cp_data[cp].data["set"]["charging_ev"] = data.ev_data["ev"+str(
                                vehicle)]
                                log.message_debug_log("debug", "Ladepunkt "+data.cp_data[cp].cp_num+", EV: "+data.cp_data[cp].data["set"]["charging_ev"].data["name"]+" (EV-Nr."+str(vehicle)+")")
            except Exception as e:
                log.exception_logging(e)
        if "all" not in data.cp_data:
            data.cp_data["all"]=chargepoint.allChargepoints()
        data.cp_data["all"].used_power_all()

    def _use_pv(self):
        """ ermittelt, ob Überschuss an der EVU vorhanden ist und kümmert sich um die Beachtung der Einspeisungsgrenze.
        """
        data.pv_data["all"].calc_power_for_control()

    def _bat(self):
        if "all" not in data.bat_module_data:
            data.bat_module_data["all"] = bat.bat()
        data.bat_module_data["all"].setup_bat()