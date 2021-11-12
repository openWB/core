""" Modul zum Updaten der Steuerung und Triggern der externen Wbs, zu updaten."""

import subprocess
import time

from . import log
from . import pub
from ..algorithm import data
from ..helpermodules import subdata


class system:
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
            pub.pub("openWB/set/system/perform_update", False)
            self.data["update_in_progress"] = True
            pub.pub("openWB/set/system/update_in_progress", True)
            if self.data["release_train"] == "stable":
                train = "stable17"
            else:
                train = self.data["release_train"]

            self._trigger_ext_update(train)
            time.sleep(15)
            # aktuell soll kein Update für den Master durchgeführt werden.
            #subprocess.run(["/var/www/html/openWB/packages/helpermodules/update_self.sh", train])
            subprocess.run("/var/www/html/openWB/runs/atreboot.sh")
        except Exception as e:
            log.MainLogger().exception("Fehler im System-Modul")

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
                        if chargepoint.data["config"]["connection_module"][
                                "selected"] == "external_openwb":
                            log.MainLogger().info("Update an LP " +
                                                  str(chargepoint.cp_num) +
                                                  " angestossen.")
                            pub.pub_single(
                                "openWB/set/system/releaseTrain",
                                train,
                                chargepoint.data["config"]["connection_module"]
                                ["config"]["external_openwb"]["ip_address"],
                                no_json=True)
                            pub.pub_single(
                                "openWB/set/system/PerformUpdate",
                                "1",
                                chargepoint.data["config"]["connection_module"]
                                ["config"]["external_openwb"]["ip_address"],
                                no_json=True)
                except Exception as e:
                    log.MainLogger().exception("Fehler im System-Modul")
        except Exception as e:
            log.MainLogger().exception("Fehler im System-Modul")


import threading
import _thread as thread
import sys


def quit_function(fn_name):
    # print to stderr, unbuffered in Python 2.
    sys.stderr.flush()  # Python 3 stderr is likely buffered.
    thread.interrupt_main()  # raises KeyboardInterrupt
    log.MainLogger().error("Ausfuehrung durch exit_after gestoppt.")


def exit_after(s):
    '''
    use as decorator to exit process if 
    function takes longer than s seconds
    '''
    def outer(fn):
        def inner(*args, **kwargs):
            timer = threading.Timer(s, quit_function, args=[fn.__name__])
            timer.start()
            try:
                result = fn(*args, **kwargs)
            finally:
                timer.cancel()
            return result

        return inner

    return outer