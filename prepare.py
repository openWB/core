""" Aufbereitung der Daten für den Algorithmus
"""

import copy

import algorithm
import data
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
        self.copy_data()
        self.check_chargepoints()
        # self.use_pv()
        # self.control.calc_current()

    def copy_data(self):
        """ kopiert die Daten, die per MQTT empfangen wurden.
        """
        data.cp_data = copy.deepcopy(subdata.subData.cp_data)
        data.cp_template_data = copy.deepcopy(subdata.subData.cp_template_data)
        for chargepoint in data.cp_data:
            if "cp" in chargepoint:
                data.cp_data[chargepoint].set_template()
                data.cp_data[chargepoint].set_topic_path(chargepoint[2:])

        data.pv_data = copy.deepcopy(subdata.subData.pv_data)
        data.pv_module_data = copy.deepcopy(subdata.subData.pv_module_data)
        data.ev_data = copy.deepcopy(subdata.subData.ev_data)
        data.ev_template_data = copy.deepcopy(subdata.subData.ev_template_data)
        data.ev_charge_template_data = copy.deepcopy(
            subdata.subData.ev_charge_template_data)
        data.counter_data = copy.deepcopy(subdata.subData.counter_data)
        data.bat_module_data = copy.deepcopy(subdata.subData.bat_module_data)
        data.general_data = copy.deepcopy(subdata.subData.general_data)
        data.optional_data = copy.deepcopy(subdata.subData.optional_data)
        data.graph_data = copy.deepcopy(subdata.subData.graph_data)

        data.print_all()

    def check_chargepoints(self):
        """ ermittelt die gewünschte Stromstärke für jeden LP.
        """
        for chargepoint in data.cp_data:
            if "cp" in chargepoint:
                if data.cp_data[chargepoint].get_state() == True:
                    # data.ev_data[data.cp_data[chargepoint].data["config"]["ev"]].get_required_current()
                    pass

    def use_pv(self):
        """ ermittelt, ob Überschuss an der EVU vorhanden ist und kümmert sich um die Beachtung der Einspeisungsgrenze.
        """
        # bisherige Skripte verwenden
        pass
