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
        self.control=algorithm.control()

    def setup_algorithm(self):
        """ bereitet die Daten für den Algorithmus vor und startet diesen.
        """
        self.copy_data()
        self.check_chargepoints()
        self.use_pv()
        self.control.calc_current()

    def copy_data(self):
        """ kopiert die Daten, die per MQTT empfangen wurden.
        """
        data.cp_data=copy.deepcopy(subdata.mqtt.cp_data)
        data.cp_template_data=copy.deepcopy(subdata.mqtt.cp_template_data)
        data.pv_data=copy.deepcopy(subdata.mqtt.pv_data)
        data.pv_module_data=copy.deepcopy(subdata.mqtt.pv_module_data)
        data.ev_data=copy.deepcopy(subdata.mqtt.ev_data)
        data.ev_template_data=copy.deepcopy(subdata.mqtt.ev_template_data)
        data.ev_charge_template_data=copy.deepcopy(subdata.mqtt.ev_charge_template_data)
        data.meter_data=copy.deepcopy(subdata.mqtt.meter_data)
        data.meter_module_data=copy.deepcopy(subdata.mqtt.meter_module_data)
        data.bat_data=copy.deepcopy(subdata.mqtt.bat_data)
        data.bat_module_data=copy.deepcopy(subdata.mqtt.bat_module_data)
        data.evu_data=copy.deepcopy(subdata.mqtt.evu_data)
        data.evu_module_data=copy.deepcopy(subdata.mqtt.evu_module_data)

    def check_chargepoints(self):
        """ ermittelt die gewünschte Stromstärke für jeden LP.
        """
        for cp in data.cp_data:
            if cp.get_state()==True:
                data.ev_data[cp.config.ev].get_required_current()

    def use_pv(self):
        """ ermittelt, ob Überschuss an der EVU vorhanden ist und kümmert sich um die Beachtung der Einspeisungsgrenze.
        """
        #bisherige Skripte verwenden
        pass


