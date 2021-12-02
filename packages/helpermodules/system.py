""" Modul zum Updaten der Steuerung und Triggern der externen Wbs, zu updaten."""

from pathlib import Path
import subprocess
import time
import _thread as thread
import threading
import sys

from helpermodules import log
from helpermodules import pub
from control import data


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
                        if chargepoint.data["config"]["connection_module"]["selected"] == "external_openwb":
                            log.MainLogger().info("Update an LP "+str(chargepoint.cp_num)+" angestossen.")
                            ip_address = chargepoint.data["config"]["connection_module"]["config"]["external_openwb"][
                                "ip_address"]
                            pub.pub_single("openWB/set/system/releaseTrain", train, ip_address, no_json=True)
                            pub.pub_single("openWB/set/system/PerformUpdate", "1", ip_address, no_json=True)
                except Exception:
                    log.MainLogger().exception("Fehler im System-Modul")
        except Exception:
            log.MainLogger().exception("Fehler im System-Modul")


def quit_function(fn_name):
    sys.stderr.flush()  # Python 3 stderr is likely buffered.
    thread.interrupt_main()  # raises KeyboardInterrupt


def exit_after(s):
    ''' https://stackoverflow.com/questions/492519/timeout-on-a-function-call
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
