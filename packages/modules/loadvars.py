""" Fragt die Werte der Module ab. Nur die openWB Kits können mit mehreren Threads gleichzeitig abgefragt werden.
"""

import threading

from . import ripple_control_receiver
from ..algorithm import data
from ..helpermodules import log

from .cp import ethmpm3pm as cp_etmpm3pm
from .cp import external_openwb as cp_external_openwb
from .cp import mqtt as cp_mqtt
from .cp import modbus_evse as cp_modbus_evse
from .cp import modbus_slave as cp_modbus_slave
from .cp import ip_evse as cp_ip_evse

class loadvars:
    """ fragt die Werte der konfigurierten Module ab
    """

    def __init__(self):
        pass

    def get_values(self):
        try:
            self._get_cp()
            self._get_general()
            kits_threads = self._get_modules()
            # Start them all
            if kits_threads:
                for thread in kits_threads:
                    thread.start()

                # Wait for all to complete
                for thread in kits_threads:
                    thread.join(timeout=3)

                for thread in kits_threads:
                    if thread.is_alive() == True:
                        log.MainLogger().error(thread.name+" konnte nicht innerhalb des Timeouts die Werte abfragen, die abgefragten Werte werden nicht in der Regelung verwendet.")
        except Exception as e:
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
        except Exception as e:
            log.MainLogger().exception("Fehler im loadvars-Modul")

    def _get_virtual_counters(self):
        """ vorhandene Zähler durchgehen und je nach Konfiguration Module zur Abfrage der Werte aufrufen
        """
        try:
            virtual_threads = []
            for item in data.data.counter_data:
                thread = None
                if "counter" in item:
                    counter = data.data.counter_data[item]
                    # if counter.data["config"]["selected"] == "virtual":
                    #     thread = threading.Thread(target=c_virtual.read_virtual_counter, args=(counter,))

                    if thread is not None:
                        virtual_threads.append(thread)
            return virtual_threads
        except Exception as e:
            log.MainLogger().exception("Fehler im loadvars-Modul")

    def _get_cp(self):
        for item in data.data.cp_data:
            try:
                if "cp" in item:
                    cp = data.data.cp_data[item]
                    # Anbindung
                    if cp.data["config"]["connection_module"]["selected"] == "modbus_evse":
                        cp_modbus_evse.read_modbus_evse(cp)
                    elif cp.data["config"]["connection_module"]["selected"] == "ip_evse":
                        cp_ip_evse.read_ip_evse(cp)
                    elif cp.data["config"]["connection_module"]["selected"] == "modbus_slave":
                        cp_modbus_slave.read_modbus_slave(cp)
                    elif cp.data["config"]["connection_module"]["selected"] == "external_openwb":
                        cp_external_openwb.read_external_openwb(cp)
                    # elif cp.data["config"]["connection_module"]["selected"] == "":
                    #     (cp)
                        
                    # Display, Pushover, SocTimer eher am Ende

                    # Ladeleistungsmodul
                    if cp.data["config"]["power_module"]["selected"] == "ethmpm3pm" or cp.data["config"]["power_module"]["selected"] == "ethmpm3pm_framer":
                        cp_etmpm3pm.read_ethmpm3pm(cp)
                    elif cp.data["config"]["power_module"]["selected"] == "mqtt":
                        cp_mqtt.mqtt_state(cp)

                    # elif cp.data["config"]["power_module"]["selected"] == "":
                    #     (cp)
            except Exception as e:
                log.MainLogger().exception("Fehler im loadvars-Modul")

    def _get_general(self):
        try:
            # Beim ersten Durchlauf wird in jedem Fall eine Exception geworfen, da die Daten erstmalig ins data-Modul kopiert werden müssen.
            if data.data.general_data["general"].data["ripple_control_receiver"]["configured"] == True:
                ripple_control_receiver.read_ripple_control_receiver()
        except Exception as e:
            log.MainLogger().exception("Fehler im loadvars-Modul")

    def _get_modules(self):
        try:
            modules_threads = []
            for item in data.data.system_data:
                try:
                    if "device" in item:
                        thread = None
                        module = data.data.system_data[item]
                        thread = threading.Thread(target=module.read, args=())
                        if thread is not None:
                            modules_threads.append(thread)
                except Exception as e:
                    log.MainLogger().exception("Fehler im loadvars-Modul")
            return modules_threads
        except Exception as e:
            log.MainLogger().exception("Fehler im loadvars-Modul")