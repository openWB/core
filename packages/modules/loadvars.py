""" Fragt die Werte der Module ab. Nur die openWB Kits können mit mehreren Threads gleichzeitig abgefragt werden.
"""

import threading

from . import ripple_control_receiver
from ..algorithm import data
from ..helpermodules import log
from .bat import alpha_ess as b_alpha_ess
from .bat import mpm3pm as b_mpm3pm
from .bat import openwb as b_openwb
from .bat import saxpower as b_saxpower
from .bat import sbs25 as b_sbs25
from .bat import siemens as b_siemens
from .bat import solax as b_solax
from .bat import studer_innotec as b_studer_innotec
from .bat import sungrow as b_sungrow
from .bat import sma_sunny_island as b_sma_sunny_island
from .bat import tesvolt as b_tesvolt
from .bat import victron as b_victron
from .counter import alpha_ess as c_alpha_ess
from .counter import carlogavazzi_lan as c_carlogavazzi_lan
from .counter import e3dc as c_e3dc
from .counter import ethmpm3pm as c_ethmpm3pm
from .counter import discovergy as c_discovergy
from .counter import janitza as c_janitza
from .counter import kostal_smart_energy_meter as c_kostal_smart_energy_meter
from .counter import powerdog as c_powerdog
from .counter import rct as c_rct
from .counter import sbs25 as c_sbs25
from .counter import siemens as c_siemens
from .counter import solaredge as c_solaredge
from .counter import solax as c_solax
from .counter import sungrow as c_sungrow
from .counter import varta as c_varta
from .counter import victron as c_victron
from .counter import virtual as c_virtual
from .cp import ethmpm3pm as cp_etmpm3pm
from .cp import external_openwb as cp_external_openwb
from .cp import mqtt as cp_mqtt
from .cp import modbus_evse as cp_modbus_evse
from .cp import modbus_slave as cp_modbus_slave
from .cp import ip_evse as cp_ip_evse
from .pv import ethmpm3pm as p_ethmpm3pm
from .pv import ethsdm120 as p_ethsdm120
from .pv import huawei as p_huawei
from .pv import powerdog as p_powerdog
from .pv import siemens as p_siemens
from .pv import solax as p_solax
from .pv import studer_innotec as p_studer_innotec
from .pv import sungrow as p_sungrow
from .pv import victron as p_victron

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
            for item in data.data.counter_data:
                if "counter" in item:
                    counter = data.data.counter_data[item]
                    if counter.data["config"]["selected"] == "alpha_ess":
                        c_alpha_ess.read_alpha_ess(counter, data.data.bat_module_data["bat1"].data["config"]["config"]["alpha_ess"]["version"])
                    elif counter.data["config"]["selected"] == "carlogavazzi_lan":
                        c_carlogavazzi_lan.read_gavazzi(counter)
                    elif counter.data["config"]["selected"] == "discovergy":
                        c_discovergy.read_discovergy(counter)
                    elif counter.data["config"]["selected"] == "e3dc":
                        c_e3dc.read_e3dc(counter, data.data.bat_module_data["bat1"].data["config"]["config"]["e3dc"]["ip_address"])
                    elif counter.data["config"]["selected"] == "fronius_energy_meter":
                        pass
                    elif counter.data["config"]["selected"] == "fronius_s0":
                        pass
                    elif counter.data["config"]["selected"] == "kostal_piko":
                        pass
                    elif counter.data["config"]["selected"] == "kostal_plenticore":
                        pass
                    elif counter.data["config"]["selected"] == "kostal_smart_energy_meter":
                        c_kostal_smart_energy_meter.read_kostal_smart_energy_meter(counter)
                    elif counter.data["config"]["selected"] == "lg_ess_v1":
                        pass
                    elif counter.data["config"]["selected"] == "janitza":
                        c_janitza.read_janitza(counter)
                    elif counter.data["config"]["selected"] == "open_ems":
                        pass
                    elif counter.data["config"]["selected"] == "powerdog":
                        c_powerdog.read_powerdog(counter)
                    elif counter.data["config"]["selected"] == "powerfox":
                        pass
                    elif counter.data["config"]["selected"] == "rct":
                        c_rct.read_rct(counter)
                    elif counter.data["config"]["selected"] == "sbs25":
                        c_sbs25.read_sbs25(counter)
                    elif counter.data["config"]["selected"] == "siemens":
                        c_siemens.read_siemens(counter)
                    elif counter.data["config"]["selected"] == "sma_homemanager":
                        pass
                    elif counter.data["config"]["selected"] == "smartfox":
                        pass
                    elif counter.data["config"]["selected"] == "smartme":
                        pass
                    elif counter.data["config"]["selected"] == "solaredge":
                        c_solaredge.read_solaredge(counter)
                    elif counter.data["config"]["selected"] == "solarlog":
                        pass
                    elif counter.data["config"]["selected"] == "solarview":
                        pass
                    elif counter.data["config"]["selected"] == "solarwatt":
                        pass
                    elif counter.data["config"]["selected"] == "solarworld":
                        pass
                    elif counter.data["config"]["selected"] == "solax":
                        c_solax.read_solax(counter)
                    elif counter.data["config"]["selected"] == "solax":
                        c_sungrow.read_sungrow(counter)
                    elif counter.data["config"]["selected"] == "varta":
                        c_varta.read_varta(counter)
                    elif counter.data["config"]["selected"] == "victron":
                        c_victron.read_victron(counter)
                    elif counter.data["config"]["selected"] == "http":
                        pass
                    elif counter.data["config"]["selected"] == "json":
                        pass
                    elif counter.data["config"]["selected"] == "mpm3pm":
                        pass
                    elif counter.data["config"]["selected"] == "sdm630":
                        pass
                    elif counter.data["config"]["selected"] == "vz_logger":
                        pass
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
                    if counter.data["config"]["selected"] == "virtual":
                        thread = threading.Thread(target=c_virtual.read_virtual_counter, args=(counter,))

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
                    # elif pv.data["config"]["selected"] == "discovergy":
                    #     (pv)
                    
                    # elif pv.data["config"]["selected"] == "fronius_energy_meter":
                    #     (pv)
                    # elif pv.data["config"]["selected"] == "fronius":
                    #     (pv)
                    # elif pv.data["config"]["selected"] == "http":
                    #     (pv)
                    if pv.data["config"]["selected"] == "huawei":
                        p_huawei.read_huawei(pv)
                    # elif pv.data["config"]["selected"] == "json":
                    #     (pv)
                    # elif pv.data["config"]["selected"] == "kostal_piko":
                    #     (pv)
                    # elif pv.data["config"]["selected"] == "kostal_piko_deprecated":
                    #     (pv)
                    # elif pv.data["config"]["selected"] == "lg_ess_v1":
                    #     (pv)
                    # elif pv.data["config"]["selected"] == "mqtt":
                    #     (pv)
                    # elif pv.data["config"]["selected"] == "kostal_plenticore":
                    #     (pv)
                    elif pv.data["config"]["selected"] == "powerdog":
                        p_powerdog.read_powerdog(pv)
                    # elif pv.data["config"]["selected"] == "powerwall":
                    #     (pv)
                    # elif pv.data["config"]["selected"] == "rct":
                    #     (pv)
                    # elif pv.data["config"]["selected"] == "shelly":
                    #     (pv)
                    elif pv.data["config"]["selected"] == "siemens":
                        p_siemens.read_siemens(pv)
                    # elif pv.data["config"]["selected"] == "smartme":
                    #     (pv)
                    # elif pv.data["config"]["selected"] == "solaredge":
                    #     (pv)
                    # elif pv.data["config"]["selected"] == "solarlog":
                    #     (pv)
                    # elif pv.data["config"]["selected"] == "solarview":
                    #     (pv)
                    # elif pv.data["config"]["selected"] == "solarwatt":
                    #     (pv)
                    # elif pv.data["config"]["selected"] == "solarworld":
                    #     (pv)
                    elif pv.data["config"]["selected"] == "solax":
                        p_solax.read_solax(pv)
                    elif pv.data["config"]["selected"] == "studer_innotec":
                        p_studer_innotec.read_studer_innotec(pv)
                    elif pv.data["config"]["selected"] == "sungrow":
                        p_sungrow.read_sungrow(pv)
                    # elif pv.data["config"]["selected"] == "sunwaves":
                    #     (pv)
                    # elif pv.data["config"]["selected"] == "sunways":
                    #     (pv)
                    # elif pv.data["config"]["selected"] == "tripower":
                    #     (pv)
                    elif pv.data["config"]["selected"] == "victron":
                        p_victron.read_victron(pv)
                    # elif pv.data["config"]["selected"] == "youless":
                    #     (pv)
                    # elif pv.data["config"]["selected"] == "smamodbus":
                    #     (pv)
                    # elif pv.data["config"]["selected"] == "vz_logger":
                    #     (pv)
            except Exception as e:
                log.exception_logging(e)

    def _get_bat(self):
        for item in data.data.bat_module_data:
            try:
                if "bat" in item:
                    bat = data.data.bat_module_data[item]
                    if bat.data["config"]["selected"] == "alpha_ess":
                        b_alpha_ess.read_alpha_ess(bat)
                    # elif bat.data["config"]["selected"] == "byd":
                    #     (bat)
                    # elif bat.data["config"]["selected"] == "e3dc":
                    #     (bat)
                    # elif bat.data["config"]["selected"] == "fronius_energy_meter":
                    #     (bat)
                    # elif bat.data["config"]["selected"] == "fronius":
                    #     (bat)
                    # elif bat.data["config"]["selected"] == "kostal_plenticore":
                    #     (bat)
                    # elif bat.data["config"]["selected"] == "lg_ess":
                    #     (bat)
                    elif bat.data["config"]["selected"] == "mpm3pm":
                        b_mpm3pm.read_mpm3pm(bat)
                    # elif bat.data["config"]["selected"] == "open_ems":
                    #     (bat)
                    elif bat.data["config"]["selected"] == "openwb":
                        b_openwb.read_openwb(bat)
                    # elif bat.data["config"]["selected"] == "rct":
                    #     (bat)
                    elif bat.data["config"]["selected"] == "saxpower":
                        b_saxpower.read_saxpower(bat)
                    elif bat.data["config"]["selected"] == "sbs25":
                        b_sbs25.read_sbs25(bat)
                    elif bat.data["config"]["selected"] == "siemens":
                        b_siemens.read_siemens(bat)
                    # elif bat.data["config"]["selected"] == "sma_sunny_boy":
                    #     (bat)
                    elif bat.data["config"]["selected"] == "sma_sunny_island":
                        b_sma_sunny_island.read_sma_sunny_island(bat)
                    # elif bat.data["config"]["selected"] == "solaredge":
                    #     (bat)
                    # elif bat.data["config"]["selected"] == "solarwatt":
                    #     (bat)
                    elif bat.data["config"]["selected"] == "solax":
                        b_solax.read_solax(bat)
                    # elif bat.data["config"]["selected"] == "sonnen_eco":
                    #     (bat)
                    elif bat.data["config"]["selected"] == "studer_innotec":
                        b_studer_innotec.read_studer_innotec(bat)
                    elif bat.data["config"]["selected"] == "sungrow":
                        b_sungrow.read_sungrow(bat)
                    # elif bat.data["config"]["selected"] == "powerwall":
                    #     (bat)
                    elif bat.data["config"]["selected"] == "tesvolt":
                        b_tesvolt.read_tesvolt(bat)
                    # elif bat.data["config"]["selected"] == "varta":
                    #     (bat)
                    elif bat.data["config"]["selected"] == "victron":
                        b_victron.read_victron(bat)
                    # elif bat.data["config"]["selected"] == "http":
                    #     (bat)
                    # elif bat.data["config"]["selected"] == "json":
                    #     (bat)
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
            for item in data.data.counter_data:
                try:
                    if "counter" in item:
                        thread = None
                        counter = data.data.counter_data[item]
                        if counter.data["config"]["selected"] == "openwb":
                            thread = threading.Thread(target=c_ethmpm3pm.read_ethmpm3pm, args=(counter,))
                        if thread != None:
                            kits_threads.append(thread)
                except Exception as e:
                    log.exception_logging(e)
            for item in data.data.pv_data:
                try:
                    if "pv" in item:
                        thread = None
                        pv = data.data.pv_data[item]
                        if pv.data["config"]["selected"] == "openwb_pv_kit" or pv.data["config"]["selected"] == "openwb_evu_kit":
                            thread = threading.Thread(target=p_ethmpm3pm.read_ethmpm3pm, args=(pv,))
                        elif pv.data["config"]["selected"] == "ethsdm120":
                            thread = threading.Thread(target=p_ethsdm120.read_ethsdm120, args=(pv,))
                        if thread != None:
                            kits_threads.append(thread)
                except Exception as e:
                    log.exception_logging(e)
            for item in data.data.bat_module_data:
                try:
                    if "bat" in item:
                        thread = None
                        bat = data.data.bat_module_data[item]
                        if bat.data["config"]["selected"] == "openwb":
                            thread = threading.Thread(target=b_openwb.read_openwb, args=(bat,))
                        if thread != None:
                            kits_threads.append(thread)
                except Exception as e:
                    log.exception_logging(e)
            return kits_threads
        except Exception as e:
            log.exception_logging(e)