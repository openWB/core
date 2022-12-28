""" Modul zum Updaten der Steuerung und Triggern der externen Wbs, zu updaten."""

import logging
import os
import subprocess
import time
from pathlib import Path


from helpermodules import pub
from control import data

log = logging.getLogger(__name__)


class System:
    def __init__(self):
        """
        """
        self.data = {}
        self.data["update_in_progress"] = False
        self.data["perform_update"] = False

    def perform_update(self):
        """ markiert ein aktives Update, triggert das Update auf dem Master und den externen WBs.
        """
        try:
            pub.Pub().pub("openWB/set/system/perform_update", False)
            self.data["update_in_progress"] = True
            pub.Pub().pub("openWB/set/system/update_in_progress", True)
            if self.data["release_train"] == "stable":
                train = "stable17"
            else:
                train = self.data["release_train"]

            self._trigger_ext_update(train)
            time.sleep(15)
            # aktuell soll kein Update für den Master durchgeführt werden.
            # subprocess.run([str(Path(__file__).resolve().parents[2]/"runs"/"update_self.sh"), train])
            subprocess.run(str(Path(__file__).resolve().parents[2]/"runs"/"atreboot.sh"))
        except Exception:
            log.exception("Fehler im System-Modul")

    def _trigger_ext_update(self, train):
        """ triggert das Update auf den externen WBs.

        Parameter
        ---------
        train: str
            Version, die geladen werden soll (Nightly, Beta, Stable)
        """
        try:
            for cp in data.data.cp_data:
                try:
                    if "cp" in cp:
                        chargepoint = data.data.cp_data[cp]
                        if chargepoint.chargepoint_module.connection_module["type"] == "external_openwb":
                            log.info("Update an LP "+str(chargepoint.num)+" angestoßen.")
                            ip_address = chargepoint.chargepoint_module.connection_module["configuration"][
                                "ip_address"]
                            pub.pub_single("openWB/config/set/releaseTrain", train, ip_address, no_json=True)
                            pub.pub_single("openWB/set/system/PerformUpdate", "1", ip_address, no_json=True)
                except Exception:
                    log.exception("Fehler im System-Modul")
        except Exception:
            log.exception("Fehler im System-Modul")

    def update_ip_address(self) -> None:
        with os.popen("ip route get 1 | awk '{print $7}'") as process:
            new_ip = process.readline().rstrip("\n")
        if new_ip != self.data["ip_address"] and new_ip != "":
            self.data["ip_address"] = new_ip
            pub.Pub().pub("openWB/set/system/ip_address", new_ip)
