#!/usr/bin/env python3
import sys


try:
    from ...helpermodules import log
    from ...helpermodules import simcount
    from ..common import connect_tcp
    from ..common import lovato
    from ..common import mpm3pm
    from ..common import sdm630
    from ..common import store
except:
    from pathlib import Path
    import os
    parentdir2 = str(Path(os.path.abspath(__file__)).parents[2])
    sys.path.insert(0, parentdir2)
    from helpermodules import log
    from helpermodules import simcount
    from modules.common import store
    from modules.common import connect_tcp
    from modules.common import lovato
    from modules.common import mpm3pm
    from modules.common import sdm630


class EvuKitFlex():
    def __init__(self, device_config: dict, component_config: dict) -> None:
        try:
            self.data = {}
            self.data["config"] = component_config
            self.data["device_config"] = device_config
            version = self.data["config"]["configuration"]["version"]
            ip_address = self.data["device_config"]["configuration"]["ip_address"]
            port = self.data["device_config"]["configuration"]["port"]
            self.data["simulation"] = {}
            self.client = connect_tcp.ConnectTcp(self.data["config"]["name"], ip_address, port)
            factory = self.__counter_factory(version)
            self.counter = factory(self.data["config"], self.client)
            self.value_store = (store.ValueStoreFactory().get_storage("counter"))()
            simcount_factory = simcount.SimCountFactory().get_sim_counter()
            self.sim_count = simcount_factory()
        except:
            log.MainLogger().exception("Fehler im Modul "+self.data["config"]["name"])

    def __counter_factory(self, version: int):
        try:
            if version == 0:
                return mpm3pm.Mpm3pm
            elif version == 1:
                return lovato.Lovato
            elif version == 2:
                return sdm630.Sdm630
        except:
            log.MainLogger().exception("Fehler im Modul "+self.data["config"]["name"])

    def read(self):
        """ liest die Werte des Moduls aus.
        """
        try:
            log.MainLogger().debug("Start kit reading")
            voltages = self.counter.get_voltage()
            power_per_phase, power_all = self.counter.get_power()
            with open("/var/www/html/openWB/ramdisk/wattbezug", "w") as f:
                f.write(str(power_all))
            frequency = self.counter.get_frequency()
            power_factors = self.counter.get_power_factor()

            if self.data["config"]["configuration"]["version"] == 0:
                try:
                    if None not in power_per_phase and None not in voltages:
                        currents = [(power_per_phase[i]/voltages[i]) for i in range(3)]
                    else:
                        currents = [0, 0, 0]
                except:
                    log.MainLogger().exception("Fehler im Modul "+self.data["config"]["name"])
                    currents = [0, 0, 0]
                imported = self.counter.get_imported()
                exported = self.counter.get_exported()
            else:
                currents = self.counter.get_current()
                if None not in currents:
                    currents = [abs(currents[i]) for i in range(3)]
                else:
                    currents = [0, 0, 0]
                log.MainLogger().debug("EVU-Kit Leistung[W]: "+str(power_all))
                topic_str = "openWB/set/system/devices/" +str(self.data["config"]["id"])+"/components/"+str(self.data["config"]["components"]["component0"]["id"])+"/"
                imported, exported = self.sim_count.sim_count(power_all, topic=topic_str, data=self.data["simulation"], prefix="bezug")

            self.value_store.set(self.data["config"]["components"]["component0"]["id"], voltages=voltages, currents=currents, powers=power_per_phase, power_factors=power_factors, imported=imported, exported=exported, power_all=power_all, frequency=frequency)
            log.MainLogger().debug("Stop kit reading "+str(power_all))
        except:
            log.MainLogger().exception("Fehler im Modul "+self.data["config"]["name"])
