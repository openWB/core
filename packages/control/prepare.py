""" Aufbereitung der Daten für den Algorithmus
"""

import logging

from control import data


log = logging.getLogger(__name__)


class Prepare:
    def __init__(self):
        pass

    def setup_algorithm(self) -> None:
        """ bereitet die Daten für den Algorithmus vor und startet diesen.
        """
        try:
            for counter in data.data.counter_data:
                if "counter" in counter:
                    data.data.counter_data[counter].setup_counter()
            for cp in data.data.cp_data.values():
                cp.update(data.data.ev_data)
            data.data.cp_all_data.get_cp_sum()
            data.data.cp_all_data.no_charge()
            data.data.bat_data["all"].setup_bat()
            data.data.counter_all_data.set_home_consumption()
        except Exception:
            log.exception("Fehler im Prepare-Modul")
        data.data.print_all()
