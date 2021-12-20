""" Fragt die Werte der Module ab. Nur die openWB Kits können mit mehreren Threads gleichzeitig abgefragt werden.
"""

import threading
from typing import Callable, List


from control import data
from control import chargepoint
from helpermodules.log import MainLogger

from modules import ripple_control_receiver


def get_hardware_values():
    __get_values([_get_cp, _get_general, _get_modules, _get_soc])


def get_virtual_values():
    """ Virtuelle Module ermitteln die Werte rechnerisch auf Bais der Messwerte anderer Module.
    Daher können sie erst die Werte ermitteln, wenn die physischen Module ihre Werte ermittelt haben.
    Würde man allle Module parallel abfragen, wären die virtuellen Module immer einen Zyklus hinterher.
    """
    __get_values([_get_virtual_counters])


def __get_values(value_funcs: List[Callable]):
    try:
        threads = []
        for func in value_funcs:
            threads.extend(func())
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


def _get_virtual_counters():
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


def _get_cp() -> List[threading.Thread]:
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
    except Exception:
        MainLogger().exception("Fehler im loadvars-Modul")
    finally:
        return modules_threads


def _get_general() -> List[threading.Thread]:
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


def _get_modules() -> List[threading.Thread]:
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


def _get_soc() -> List[threading.Thread]:
    modules_threads = []  # type: List[threading.Thread]
    try:
        for ev in data.data.ev_data.values():
            # Ist das Auto einem LP zugeordnet?
            for cp in data.data.cp_data.values():
                if isinstance(cp, chargepoint.Chargepoint):
                    if cp.data["set"]["charging_ev"] == ev.ev_num:
                        cp_state = cp.data
                        charge_state = cp.data["get"]["charge_state"]
                        plug_state = cp.data["get"]["plug_state"]
                        break
            else:
                cp_state, plug_state, charge_state = None,  None, None
            if ev.ev_template.soc_interval_expired(plug_state, charge_state, ev.data["get"].get(
                    "timestamp_last_request")):
                modules_threads.append(threading.Thread(target=ev.soc_module.update, args=(cp_state,)))
    except Exception:
        MainLogger().exception("Fehler im loadvars-Modul")
    finally:
        return modules_threads
