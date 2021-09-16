""" Modul zum Updaten der Steuerung und Triggern der externen Wbs, zu updaten."""

import subprocess
import time

from . import log
from . import pub
from ..algorithm import data

class system:
    def __init__(self):
        """
        """
        self.data = {}
        self.data["update_in_progress"] = False
        self.data["perform_update"] = False

    def perform_update(self, ):
        """
        """
        self.data["update_in_progress"] = True
        pub.pub("openWB/set/system/update_in_progress", True)
        if data.data.system_data["release_train"] == "stable":
            train = "stable17"
        else:
            train = data.data.system_data["release_train"]

        self._trigger_ext_update(train)
        time.sleep(15)
        # aktuell soll kein Update für den Master durchgeführt werden.
        #subprocess.Popen(["/var/www/html/openWB/packages/helpermodules/update_self.sh", train])
        subprocess.Popen("/var/www/html/openWB/runs/atreboot.sh")

    def _trigger_ext_update(self, train):
        """
        """
        for cp in data.data.cp_data:
            if "cp" in cp:
                chargepoint = data.data.cp_data[cp]
                if chargepoint.data["config"]["connection_module"]["selected"] == "external_openwb":
                    log.message_debug_log("info", "Update an LP "+str(chargepoint.cp_num)+" angestossen.")
                    pub.pub_single("openWB/set/system/releaseTrain", data.data.system_data["release_train"], chargepoint.data["config"]["connection_module"]["config"]["external_openwb"]["ip_address"], no_json=True)
                    pub.pub_single("openWB/set/system/PerformUpdate", "1", chargepoint.data["config"]["connection_module"]["config"]["external_openwb"]["ip_address"], no_json=True)