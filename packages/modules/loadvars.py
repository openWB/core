"""
"""

import threading

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


class loadvars():
    """ fragt die Werte der konfigurierten Module ab
    """

    def __init__(self):
        pass

    def get_values(self):
        try:
            all_threads = []
            counter_threads = self.get_counters()
            if counter_threads:
                all_threads.extend(counter_threads)
            self.get_cp()
            self.get_pv()
            self.get_bat()
            self.get_soc()
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

    def get_counters(self):
        """ vorhandene Zähler durchgehen und je nach Konfiguration Module zur Abfrage der Werte aufrufen
        """
        try:
            counter_threads = []
            for item in data.data.counter_data:
                if "counter" in item:
                    counter = data.data.counter_data[item]
                    if counter.data["config"]["selected"] == "openwb":
                        thread = threading.Thread(target=c_ethmpm3pm.read_ethmpm3pm, args=(counter,))
                    elif counter.data["config"]["selected"] == "alpha_ess":
                        thread = threading.Thread(target=c_alpha_ess.read_alpha_ess, args=(counter, data.data.bat_module_data["bat1"].data["config"]["config"]["alpha_ess"]["version"]))
                    elif counter.data["config"]["selected"] == "carlogavazzi_lan":
                        thread = threading.Thread(target=c_carlogavazzi_lan.read_gavazzi, args=(counter,))
                    elif counter.data["config"]["selected"] == "discovergy":
                        thread = threading.Thread(target=c_discovergy.read_discovergy, args=(counter,))
                    elif counter.data["config"]["selected"] == "e3dc":
                        thread = threading.Thread(target=c_e3dc.read_e3dc, args=(counter, data.data.bat_module_data["bat1"].data["config"]["config"]["e3dc"]["ip_address"]))
                    elif counter.data["config"]["selected"] == "fronius_energy_meter":
                        pass
                    elif counter.data["config"]["selected"] == "fronius_s0":
                        pass
                    elif counter.data["config"]["selected"] == "kostal_piko":
                        pass
                    elif counter.data["config"]["selected"] == "kostal_plenticore":
                        pass
                    elif counter.data["config"]["selected"] == "kostal_smart_energy_meter":
                        thread = threading.Thread(target=c_kostal_smart_energy_meter.read_kostal_smart_energy_meter, args=(counter,))
                    elif counter.data["config"]["selected"] == "lg_ess_v1":
                        pass
                    elif counter.data["config"]["selected"] == "janitza":
                        thread = threading.Thread(target=c_janitza.read_janitza, args=(counter,))
                    elif counter.data["config"]["selected"] == "open_ems":
                        pass
                    elif counter.data["config"]["selected"] == "powerdog":
                        thread = threading.Thread(target=c_powerdog.read_powerdog, args=(counter,))
                    elif counter.data["config"]["selected"] == "powerfox":
                        pass
                    elif counter.data["config"]["selected"] == "rct":
                        thread = threading.Thread(target=c_rct.read_rct, args=(counter,))
                    elif counter.data["config"]["selected"] == "sbs25":
                        thread = threading.Thread(target=c_sbs25.read_sbs25, args=(counter,))
                    elif counter.data["config"]["selected"] == "siemens":
                        thread = threading.Thread(target=c_siemens.read_siemens, args=(counter,))
                    elif counter.data["config"]["selected"] == "sma_homemanager":
                        pass
                    elif counter.data["config"]["selected"] == "smartfox":
                        pass
                    elif counter.data["config"]["selected"] == "smartme":
                        pass
                    elif counter.data["config"]["selected"] == "solaredge":
                        thread = threading.Thread(target=c_solaredge.read_solaredge, args=(counter,))
                    elif counter.data["config"]["selected"] == "solarlog":
                        pass
                    elif counter.data["config"]["selected"] == "solarview":
                        pass
                    elif counter.data["config"]["selected"] == "solarwatt":
                        pass
                    elif counter.data["config"]["selected"] == "solarworld":
                        pass
                    elif counter.data["config"]["selected"] == "solax":
                        thread = threading.Thread(target=c_solax.read_solax, args=(counter,))
                    elif counter.data["config"]["selected"] == "solax":
                        thread = threading.Thread(target=c_sungrow.read_sungrow, args=(counter,))
                    elif counter.data["config"]["selected"] == "varta":
                        thread = threading.Thread(target=c_varta.read_varta, args=(counter,))
                    elif counter.data["config"]["selected"] == "victron":
                        thread = threading.Thread(target=c_victron.read_victron, args=(counter,))
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
                    
                    counter_threads.append(thread)
            return counter_threads
        except Exception as e:
            log.exception_logging(e)

    def get_cp(self):
        pass

    def get_pv(self):
        pass

    def get_bat(self):
        bat_threads = []
        for item in data.data.bat_module_data:
            try:
                if "bat" in item:
                    bat = data.data.bat_module_data[item]
                    if bat.data["config"]["selected"] == "openwb":
                        pass
                        #thread = threading.Thread(target=, args=(bat,))
                    elif bat.data["config"]["selected"] == "alpha_ess":
                        thread = threading.Thread(target=b_alpha_ess.read_alpha_ess, args=(bat,))
                    # elif bat.data["config"]["selected"] == "byd":
                    #     thread = threading.Thread(target=, args=(bat,))
                    # elif bat.data["config"]["selected"] == "e3dc":
                    #     thread = threading.Thread(target=, args=(bat,))
                    # elif bat.data["config"]["selected"] == "fronius_energy_meter":
                    #     thread = threading.Thread(target=, args=(bat,))
                    # elif bat.data["config"]["selected"] == "fronius":
                    #     thread = threading.Thread(target=, args=(bat,))
                    # elif bat.data["config"]["selected"] == "kostal_plenticore":
                    #     thread = threading.Thread(target=, args=(bat,))
                    # elif bat.data["config"]["selected"] == "lg_ess":
                    #     thread = threading.Thread(target=, args=(bat,))
                    elif bat.data["config"]["selected"] == "mpm3pm":
                        thread = threading.Thread(target=b_mpm3pm.read_mpm3pm, args=(bat,))
                    # elif bat.data["config"]["selected"] == "open_ems":
                    #     thread = threading.Thread(target=, args=(bat,))
                    elif bat.data["config"]["selected"] == "openwb":
                        thread = threading.Thread(target=b_openwb.read_openwb, args=(bat,))
                    # elif bat.data["config"]["selected"] == "rct":
                    #     thread = threading.Thread(target=, args=(bat,))
                    elif bat.data["config"]["selected"] == "saxpower":
                        thread = threading.Thread(target=b_saxpower.read_saxpower, args=(bat,))
                    elif bat.data["config"]["selected"] == "sbs25":
                        thread = threading.Thread(target=b_sbs25.read_sbs25, args=(bat,))
                    elif bat.data["config"]["selected"] == "siemens":
                        thread = threading.Thread(target=b_siemens.read_siemens, args=(bat,))
                    # elif bat.data["config"]["selected"] == "sma_sunny_boy":
                    #     thread = threading.Thread(target=, args=(bat,))
                    elif bat.data["config"]["selected"] == "sma_sunny_island":
                        thread = threading.Thread(target=b_sma_sunny_island.read_sma_sunny_island, args=(bat,))
                    # elif bat.data["config"]["selected"] == "solaredge":
                    #     thread = threading.Thread(target=, args=(bat,))
                    # elif bat.data["config"]["selected"] == "solarwatt":
                    #     thread = threading.Thread(target=, args=(bat,))
                    elif bat.data["config"]["selected"] == "solax":
                        thread = threading.Thread(target=b_solax.read_solax, args=(bat,))
                    # elif bat.data["config"]["selected"] == "sonnen_eco":
                    #     thread = threading.Thread(target=, args=(bat,))
                    elif bat.data["config"]["selected"] == "studer_innotec":
                        thread = threading.Thread(target=b_studer_innotec.read_studer_innotec, args=(bat,))
                    elif bat.data["config"]["selected"] == "sungrow":
                        thread = threading.Thread(target=b_sungrow.read_sungrow, args=(bat,))
                    # elif bat.data["config"]["selected"] == "powerwall":
                    #     thread = threading.Thread(target=, args=(bat,))
                    elif bat.data["config"]["selected"] == "tesvolt":
                        thread = threading.Thread(target=b_tesvolt.read_tesvolt, args=(bat,))
                    # elif bat.data["config"]["selected"] == "varta":
                    #     thread = threading.Thread(target=, args=(bat,))
                    elif bat.data["config"]["selected"] == "victron":
                        thread = threading.Thread(target=b_victron.read_victron, args=(bat,))
                    # elif bat.data["config"]["selected"] == "http":
                    #     thread = threading.Thread(target=, args=(bat,))
                    # elif bat.data["config"]["selected"] == "json":
                    #     thread = threading.Thread(target=, args=(bat,))
                    bat_threads.append(thread)
            except Exception as e:
                log.exception_logging(e)
        return bat_threads

    def get_soc(self):
        pass
