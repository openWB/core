""" Verschachtelte Listen, die die Daten zur Berechnung des Alogrithmus enthalten.
Dictionary: Zugriff erfolgt bei Dictionary über Keys, nicht über Indizes wie bei Listen. Das hat den Vorteil, dass Instanzen gelöscht werden können, der Zugriff aber nicht verändert werden musss.
"""

import json

cp_data={}
cp_template_data={}
pv_data={}
pv_module_data={}
ev_data={}
ev_template_data={}
ev_charge_template_data={}
counter_data={}
counter_module_data={}
bat_module_data={}
evu_data={}
evu_module_data={}
general_data={}
optional_data={}
graph_data={}

class data():
    """
    """

    @classmethod
    def print_all(self):
        print(json.dumps(vars(data), indent=4))