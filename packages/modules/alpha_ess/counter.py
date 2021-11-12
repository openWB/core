#!/usr/bin/env python3
import time
from typing import List, Tuple

try:
    from ...helpermodules import log
    from ..common import connect_tcp
    from ..common import store
except Exception:
    from pathlib import Path
    import os
    import sys
    parentdir2 = str(Path(os.path.abspath(__file__)).parents[2])
    sys.path.insert(0, parentdir2)
    from helpermodules import log
    from modules.common import store
    from modules.common import connect_tcp


def get_default() -> dict:
    return {
        "name": "Alpha ESS Zähler",
        "id": None,
        "type": "counter",
        "configuration":
        {
            "version": 1
        }
    }


class AlphaEssCounter():
    def __init__(self, client: connect_tcp.ConnectTcp, component_config: dict) -> None:
        try:
            self.client = client
            self.data["config"] = component_config
            self.value_store = (
                store.ValueStoreFactory().get_storage("counter"))()
        except Exception as e:
            log.MainLogger().error("Fehler im Modul " +
                                   self.data["config"]["name"], e)

    def read(self):
        try:
            log.MainLogger().debug(
                "Komponente "+self.data["config"]["name"]+" auslesen.")
            time.sleep(0.1)
            factory_method = self.__version_factory(
                self.data["config"]["configuration"]["version"])
            power_all, exported, imported, currents = factory_method(sdmid=85)

            self.value_store.set(self.data["config"]["id"], voltages=[0, 0, 0], currents=currents, powers=[
                                 0, 0, 0], power_factors=[0, 0, 0], imported=imported, exported=exported, power_all=power_all, frequency=50)
        except Exception as e:
            log.MainLogger().error("Fehler im Modul " +
                                   self.data["config"]["name"], e)

    def __version_factory(self, version: int):
        try:
            if version == 0:
                return self.__read_before_v123
            else:
                return self.__read_since_v123
        except Exception as e:
            log.MainLogger().error("Fehler im Modul " +
                                   self.data["config"]["name"], e)

    def __read_before_v123(self, sdmid: int) -> Tuple[float, float, float, List[float]]:
        try:
            power_all = self.client.read_binary_registers_to_int(
                0x0006, 4, sdmid, 32)
            exported = self.client.read_binary_registers_to_int(
                0x0008, 4, sdmid, 32)
            if exported is not None:
                exported = exported * 10
            imported = self.client.read_binary_registers_to_int(
                0x000A, 4, sdmid, 32)
            if imported is not None:
                imported = imported * 10
            currents = []
            regs = [0x0000, 0x0002, 0x0004]
            for register in regs:
                value = self.client.read_binary_registers_to_int(
                    register, 4, sdmid, 32)
                if value is not None:
                    value = value / 230
                currents.append(value)
            return power_all, exported, imported, currents
        except Exception as e:
            log.MainLogger().error("Fehler im Modul " +
                                   self.data["config"]["name"], e)

    def __read_since_v123(self, sdmid: int) -> Tuple[float, float, float, List[float]]:
        try:
            power_all = self.client.read_binary_registers_to_int(
                0x0021, 4, sdmid, 32)
            exported = self.client.read_binary_registers_to_int(
                0x0010, 4, sdmid, 32)
            if exported is not None:
                exported = exported * 10
            imported = self.client.read_binary_registers_to_int(
                0x0012, 4, sdmid, 32)
            if imported is not None:
                imported = imported * 10
            currents = []
            regs = [0x0017, 0x0018, 0x0019]
            for register in regs:
                value = self.client.read_binary_registers_to_int(
                    register, 2, sdmid, 16)
                if value is not None:
                    value = value / 1000
                currents.append(value)
            return power_all, exported, imported, currents
        except Exception as e:
            log.MainLogger().error("Fehler im Modul " +
                                   self.data["config"]["name"], e)
