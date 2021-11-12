#!/usr/bin/env python3
import time

try:
    from ...helpermodules import log
    from ...helpermodules import simcount
    from ..common import connect_tcp
    from ..common import store
except Exception:
    from pathlib import Path
    import os
    import sys
    parentdir2 = str(Path(os.path.abspath(__file__)).parents[2])
    sys.path.insert(0, parentdir2)
    from helpermodules import log
    from helpermodules import simcount
    from modules.common import connect_tcp
    from modules.common import store


def get_default() -> dict:
    return {
        "name": "Alpha ESS Wechselrichter",
        "id": None,
        "type": "inverter",
        "configuration":
        {
            "version": 1
        }
    }


class AlphaEssInverter():
    def __init__(self, component_config: dict, tcp_client) -> None:
        try:
            self.client = tcp_client
            self.data = {}
            self.data["config"] = component_config
            self.data["simulation"] = {}
            self.value_store = (
                store.ValueStoreFactory().get_storage("inverter"))()
            simcount_factory = simcount.SimCountFactory().get_sim_counter()
            self.sim_count = simcount_factory()
        except Exception as e:
            log.MainLogger().error("Fehler im Modul " +
                                   self.data["config"]["name"], e)

    def read(self):
        try:
            log.MainLogger().debug(
                "Komponente "+self.data["config"]["name"]+" auslesen.")
            reg_p = self.__version_factory(
                self.data["config"]["configuration"]["version"])
            power = self.__get_power(85, reg_p)

            if power is not None:
                _, counter = self.sim_count.sim_count(power, topic="openWB/set/pv/"+str(
                    self.data["config"]["id"])+"/", data=self.data["simulation"], prefix="pv")
            else:
                counter = None
            self.value_store.set(
                self.data["config"]["id"], power=power, counter=counter, currents=[0, 0, 0])
        except Exception as e:
            log.MainLogger().error("Fehler im Modul " +
                                   self.data["config"]["name"], e)

    def __version_factory(self, version: int) -> int:
        try:
            if version == 0:
                return 0x0012
            else:
                return 0x00A1
        except Exception as e:
            log.MainLogger().error("Fehler im Modul " +
                                   self.data["config"]["name"], e)

    def __get_power(self, sdmid: int, reg_p: int) -> float:
        try:
            p_reg = self.client.read_binary_registers_to_int(
                reg_p, 4, sdmid, 32)
            if p_reg is not None:
                if (p_reg < 0):
                    p_reg = p_reg * -1
            time.sleep(0.1)
            p2_reg = self.client.read_binary_registers_to_int(
                0x041F, 4, sdmid, 32)
            p3_reg = self.client.read_binary_registers_to_int(
                0x0423, 4, sdmid, 32)
            p4_reg = self.client.read_binary_registers_to_int(
                0x0427, 4, sdmid, 32)
            if p2_reg is not None and p3_reg is not None and p4_reg is not None:
                power = (p_reg + p2_reg + p3_reg + p4_reg) * -1
            else:
                power = None
            log.MainLogger().debug("Alpha Ess Leistung: "+str(power)+", WR-Register: R1" +
                                   str(p_reg)+" R2 "+str(p2_reg)+" R3 "+str(p3_reg)+" R4 "+str(p4_reg))
            return power
        except Exception as e:
            log.MainLogger().error("Fehler im Modul " +
                                   self.data["config"]["name"], e)
