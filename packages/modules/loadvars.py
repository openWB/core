""" Fragt die Werte der Module ab. Nur die openWB Kits können mit mehreren Threads gleichzeitig abgefragt werden.
"""

import threading
from typing import List


from control import data
from helpermodules.log import MainLogger

from modules import ripple_control_receiver


class Loadvars:
    """ fragt die Werte der konfigurierten Module ab
    """

    def __init__(self):
        pass

    def get_values(self):
        try:
            threads = []
            threads.extend(self._get_cp())
            threads.extend(self._get_general())
            threads.extend(self._get_modules())
            # Start them all
            if threads:
                for thread in threads:
                    thread.start()

                # Wait for all to complete
                for thread in threads:
                    thread.join(timeout=3)

                for thread in threads:
                    if thread.is_alive():
                        MainLogger().error(
                            thread.name +
                            " konnte nicht innerhalb des Timeouts die Werte abfragen, die abgefragten Werte werden" +
                            " nicht in der Regelung verwendet.")
        except Exception:
            MainLogger().exception("Fehler im loadvars-Modul")

    # eher zu prepare
    # Hausverbrauch
    # Überschuss unter Beachtung abschaltbarer SH-Devices

    def get_virtual_values(self):
        """ Virtuelle Module ermitteln die Werte rechnerisch auf Bais der Messwerte anderer Module.
        Daher können sie erst die Werte ermitteln, wenn die physischen Module ihre Werte ermittelt haben.
        Würde man allle Module parallel abfragen, wären die virtuellen Module immer einen Zyklus hinterher.
        """
        try:
            all_threads = []
            all_threads.extend(self._get_virtual_counters())
            # Start them all
            if all_threads:
                for thread in all_threads:
                    thread.start()

                # Wait for all to complete
                for thread in all_threads:
                    thread.join(timeout=3)
        except Exception:
            MainLogger().exception("Fehler im loadvars-Modul")

    def _get_virtual_counters(self):
        """ vorhandene Zähler durchgehen und je nach Konfiguration Module zur Abfrage der Werte aufrufen
        """
        modules_threads = []  # type: List[threading.Thread]
        try:
            for item in data.data.system_data:
                try:
                    if "device" in item:
                        if data.data.system_data[item].device_config["type"] == "virtual":
                            thread = None
                            module = data.data.system_data[item]
                            thread = threading.Thread(target=module.get_values, args=())
                            if thread is not None:
                                modules_threads.append(thread)
                except Exception:
                    MainLogger().exception("Fehler im loadvars-Modul")
            return modules_threads
        except Exception:
            MainLogger().exception("Fehler im loadvars-Modul")
        finally:
            return modules_threads

    def _get_cp(self):
        modules_threads = []  # type: List[threading.Thread]
        try:
            for item in data.data.cp_data:
                try:
                    if "cp" in item:
                        thread = None
                        chargepoint_module = data.data.cp_data[item].chargepoint_module
                        thread = threading.Thread(target=chargepoint_module.get_values, args=())
                        if thread is not None:
                            modules_threads.append(thread)
                except Exception:
                    MainLogger().exception("Fehler im loadvars-Modul")
            return modules_threads
        except Exception:
            MainLogger().exception("Fehler im loadvars-Modul")
        finally:
            return modules_threads

    def _get_general(self) -> List[threading.Thread]:
        threads = []  # type: List[threading.Thread]
        try:
            # Beim ersten Durchlauf wird in jedem Fall eine Exception geworfen,
            # da die Daten erstmalig ins data-Modul kopiert werden müssen.
            if data.data.general_data["general"].data[
                    "ripple_control_receiver"]["configured"]:
                threads.append(threading.Thread(target=ripple_control_receiver.read, args=()))
        except Exception:
            MainLogger().exception("Fehler im loadvars-Modul")
        finally:
            return threads

    def _get_modules(self) -> List[threading.Thread]:
        modules_threads = []  # type: List[threading.Thread]
        try:
            for item in data.data.system_data:
                try:
                    if "device" in item:
                        if data.data.system_data[item].device_config["type"] != "virtual":
                            thread = None
                            module = data.data.system_data[item]
                            thread = threading.Thread(target=module.update, args=())
                            if thread is not None:
                                modules_threads.append(thread)
                except Exception:
                    MainLogger().exception("Fehler im loadvars-Modul")
            return modules_threads
        except Exception:
            MainLogger().exception("Fehler im loadvars-Modul")
        finally:
            return modules_threads
