"""
"""

import threading

from ..algorithm import data
from ..helpermodules import log
from .counter import carlogavazzi_lan
from .counter import ethmpm3pm
from .counter import discovergy
from .counter import janitza
from .counter import kostal_smart_energy_meter
from .counter import powerdog
from .counter import rct
from .counter import sbs25
from .counter import siemens


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
                        if counter.data["config"]["config"]["openwb"]["version"] == 0:
                            thread = threading.Thread(target=ethmpm3pm.read_version0, args=(counter,))
                        elif counter.data["config"]["config"]["openwb"]["version"] == 1:
                            thread = threading.Thread(target=ethmpm3pm.read_lovato, args=(counter,))
                        elif counter.data["config"]["config"]["openwb"]["version"] == 2:
                            thread = threading.Thread(target=ethmpm3pm.read_sdm, args=(counter,))
                        else:
                            log.message_debug_log("info", "Unbekannte Version des openWB EVU Kits")
                    elif counter.data["config"]["selected"] == "alpha_ess":
                        pass
                    elif counter.data["config"]["selected"] == "carlogavazzi_lan":
                        thread = threading.Thread(target=carlogavazzi_lan.read_gavazzi, args=(counter,))
                    elif counter.data["config"]["selected"] == "discovergy":
                        thread = threading.Thread(target=discovergy.read_discovergy, args=(counter,))
                    elif counter.data["config"]["selected"] == "e3dc":
                        pass
                    elif counter.data["config"]["selected"] == "fronius_energy_meter":
                        pass
                    elif counter.data["config"]["selected"] == "fronius_s0":
                        pass
                    elif counter.data["config"]["selected"] == "kostal_piko":
                        pass
                    elif counter.data["config"]["selected"] == "kostal_plenticore":
                        pass
                    elif counter.data["config"]["selected"] == "kostal_smart_energy_meter":
                        thread = threading.Thread(target=kostal_smart_energy_meter.read_kostal_smart_energy_meter, args=(counter,))
                    elif counter.data["config"]["selected"] == "lg_ess_v1":
                        pass
                    elif counter.data["config"]["selected"] == "janitza":
                        thread = threading.Thread(target=janitza.read_janitza, args=(counter,))
                    elif counter.data["config"]["selected"] == "open_ems":
                        pass
                    elif counter.data["config"]["selected"] == "powerdog":
                        thread = threading.Thread(target=powerdog.read_powerdog, args=(counter,))
                    elif counter.data["config"]["selected"] == "powerfox":
                        pass
                    elif counter.data["config"]["selected"] == "rct":
                        thread = threading.Thread(target=rct.read_rct, args=(counter,))
                    elif counter.data["config"]["selected"] == "sbs25":
                        thread = threading.Thread(target=sbs25.read_sbs25, args=(counter,))
                    elif counter.data["config"]["selected"] == "siemens":
                        thread = threading.Thread(target=siemens.read_siemens, args=(counter,))
                    elif counter.data["config"]["selected"] == "sma_homemanager":
                        pass
                    elif counter.data["config"]["selected"] == "smartfox":
                        pass
                    elif counter.data["config"]["selected"] == "smartme":
                        pass
                    elif counter.data["config"]["selected"] == "solaredge":
                        pass
                    elif counter.data["config"]["selected"] == "solarlog":
                        pass
                    elif counter.data["config"]["selected"] == "solarview":
                        pass
                    elif counter.data["config"]["selected"] == "solarwatt":
                        pass
                    elif counter.data["config"]["selected"] == "solarworld":
                        pass
                    elif counter.data["config"]["selected"] == "solax":
                        pass
                    elif counter.data["config"]["selected"] == "varta":
                        pass
                    elif counter.data["config"]["selected"] == "victron":
                        pass
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
        pass

    def get_soc(self):
        pass
