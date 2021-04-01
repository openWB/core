""" Verschachtelte Listen, die die Daten zur Berechnung des Alogrithmus enthalten.
Dictionary: Zugriff erfolgt bei Dictionary über Keys, nicht über Indizes wie bei Listen. Das hat den Vorteil, dass Instanzen gelöscht werden können, der Zugriff aber nicht verändert werden musss.
"""

import log

cp_data = {}
cp_template_data = {}
pv_data = {}
ev_data = {}
ev_template_data = {}
ev_charge_template_data = {}
counter_data = {}
bat_module_data = {}
general_data = {}
optional_data = {}
graph_data = {}


def print_all():
    print_dictionaries(cp_data)
    print_dictionaries(cp_template_data)
    print_dictionaries(pv_data)
    print_dictionaries(ev_data)
    print_dictionaries(ev_template_data)
    print_dictionaries(ev_charge_template_data)
    print_dictionaries(counter_data)
    print_dictionaries(bat_module_data)
    print_dictionaries(general_data)
    print_dictionaries(optional_data)
    print_dictionaries(graph_data)


def print_dictionaries(data):
    """ gibt zu Debug-Zwecken für jeden Key im übergebenen Dictionary das Dictionary aus.

    Parameter
    ---------
    data: dict
    """
    try:
        for key in data:
            print(key)
            if isinstance(data[key], dict) == False:
                print(data[key].data)
            else:
                print("Klasse fehlt")
    except Exception as e:
        log.exception_logging(e)
