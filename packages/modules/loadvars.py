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

class loadvars():
    """ fragt die Werte der konfigurierten Module ab
    """

    def __init__(self):
        pass

    def get_values(self):
        try:
            all_threads = []
            self._get_cp()
            self._get_counters()
            self._get_pv()
            self._get_bat()
            self._get_soc()
            self._get_general()
            all_threads = self._get_kits()
            # Start them all
            if all_threads:
                for thread in all_threads:
                    thread.start()

                # Wait for all to complete
                for thread in all_threads:
                    thread.join(timeout=3)
        except Exception as e:
            log.exception_logging(e)

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
            log.exception_logging(e)

    def _get_counters(self):
        """ vorhandene Zähler durchgehen und je nach Konfiguration Module zur Abfrage der Werte aufrufen
        """
        try:
            for item in data.data.counter_module_data:
                counter = data.data.counter_module_data[item]
                if counter.data["module"]["selected"] != "openwb":
                    counter.read()
        except Exception as e:
            log.exception_logging(e)

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

                    if thread != None:
                        virtual_threads.append(thread)
            return virtual_threads
        except Exception as e:
            log.exception_logging(e)

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
                log.exception_logging(e)

    def _get_pv(self):
        for item in data.data.pv_data:
            try:
                if "pv" in item:
                    pv = data.data.pv_data[item]
                    pass
            except Exception as e:
                log.exception_logging(e)

    def _get_bat(self):
        for item in data.data.bat_module_data:
            try:
                if "bat" in item:
                    bat = data.data.bat_module_data[item]
            except Exception as e:
                log.exception_logging(e)

    def _get_soc(self):
        try:
            pass
        except Exception as e:
            log.exception_logging(e)

    def _get_general(self):
        try:
            if data.data.general_data["general"].data["ripple_control_receiver"]["configured"] == True:
                ripple_control_receiver.read_ripple_control_receiver()
        except Exception as e:
            log.exception_logging(e)

    def _get_kits(self):
        try:
            kits_threads = []
            for item in data.data.counter_module_data:
                try:
                    if "counter" in item:
                        thread = None
                        counter = data.data.counter_module_data[item]
                        if counter.data["module"]["selected"] == "openwb":
                            thread = threading.Thread(target=counter.read, args=())
                        if thread != None:
                            kits_threads.append(thread)
                except Exception as e:
                    log.exception_logging(e)
            for item in data.data.pv_data:
                try:
                    if "pv" in item:
                        thread = None
                        pv = data.data.pv_data[item]
                        # if pv.data["config"]["selected"] == "openwb_pv_kit" or pv.data["config"]["selected"] == "openwb_evu_kit":
                        #     thread = threading.Thread(target=p_ethmpm3pm.read_ethmpm3pm, args=(pv,))
                        # elif pv.data["config"]["selected"] == "ethsdm120":
                        #     thread = threading.Thread(target=p_ethsdm120.read_ethsdm120, args=(pv,))
                        if thread != None:
                            kits_threads.append(thread)
                except Exception as e:
                    log.exception_logging(e)
            for item in data.data.bat_module_data:
                try:
                    if "bat" in item:
                        thread = None
                        bat = data.data.bat_module_data[item]
                        # if bat.data["config"]["selected"] == "openwb":
                        #     thread = threading.Thread(target=b_openwb.read_openwb, args=(bat,))
                        if thread != None:
                            kits_threads.append(thread)
                except Exception as e:
                    log.exception_logging(e)
            return kits_threads
        except Exception as e:
            log.exception_logging(e)