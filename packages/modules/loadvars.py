""" Fragt die Werte der Module ab. Nur die openWB Kits können mit mehreren Threads gleichzeitig abgefragt werden.
"""

import threading
from typing import List, Union

from modules import ripple_control_receiver
from control import data
from helpermodules import log

from modules.cp import external_openwb as cp_external_openwb


class loadvars:
    """ fragt die Werte der konfigurierten Module ab
    """

    def __init__(self):
        pass

    def get_values(self):
        try:
            threads = []
            self._get_cp()
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
                        log.MainLogger().error(
                            thread.name +
                            " konnte nicht innerhalb des Timeouts die Werte abfragen, die abgefragten Werte werden" +
                            " nicht in der Regelung verwendet.")
        except Exception:
            log.MainLogger().exception("Fehler im loadvars-Modul")

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
            log.MainLogger().exception("Fehler im loadvars-Modul")

    def _get_virtual_counters(self):
        """ vorhandene Zähler durchgehen und je nach Konfiguration Module zur Abfrage der Werte aufrufen
        """
        try:
            virtual_threads = []
            for item in data.data.counter_data:
                thread = None
                # if "counter" in item:
                #     counter = data.data.counter_data[item]
                # if counter.data["config"]["selected"] == "virtual":
                #     thread = threading.Thread(target=c_virtual.read_virtual_counter, args=(counter,))

                if thread is not None:
                    virtual_threads.append(thread)
            return virtual_threads
        except Exception:
            log.MainLogger().exception("Fehler im loadvars-Modul")

    def _get_cp(self):
        for item in data.data.cp_data:
            try:
                if "cp" in item:
                    cp = data.data.cp_data[item]
                    # Anbindung
                    if cp.data["config"]["connection_module"][
                            "selected"] == "external_openwb":
                        cp_external_openwb.read_external_openwb(cp)
                    # elif cp.data["config"]["connection_module"]["selected"] == "":
                    #     (cp)

                    # elif cp.data["config"]["power_module"]["selected"] == "":
                    #     (cp)
            except Exception:
                log.MainLogger().exception("Fehler im loadvars-Modul")

    def _get_general(self) -> List[threading.Thread]:
        threads = []  # type: List[threading.Thread]
        try:
            # Beim ersten Durchlauf wird in jedem Fall eine Exception geworfen,
            # da die Daten erstmalig ins data-Modul kopiert werden müssen.
            if data.data.general_data["general"].data[
                    "ripple_control_receiver"]["configured"]:
                threads.append(threading.Thread(target=ripple_control_receiver.read, args=()))
        except Exception:
            log.MainLogger().exception("Fehler im loadvars-Modul")
        finally:
            return threads

    def _get_modules(self) -> List[threading.Thread]:
        modules_threads = []  # type: List[threading.Thread]
        try:
            for item in data.data.system_data:
                try:
                    if "device" in item:
                        thread = None
                        module = data.data.system_data[item]
                        thread = threading.Thread(target=module.get_values, args=())
                        if thread is not None:
                            modules_threads.append(thread)
                except Exception:
                    log.MainLogger().exception("Fehler im loadvars-Modul")
            return modules_threads
        except Exception:
            log.MainLogger().exception("Fehler im loadvars-Modul")
        finally:
            return modules_threads
