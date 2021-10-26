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
                        if chargepoint.data["config"]["connection_module"]["selected"] == "external_openwb":
                            log.MainLogger().info("Update an LP "+str(chargepoint.cp_num)+" angestossen.")
                            pub.pub_single("openWB/set/system/releaseTrain", train, chargepoint.data["config"]["connection_module"]["config"]["external_openwb"]["ip_address"], no_json=True)
                            pub.pub_single("openWB/set/system/PerformUpdate", "1", chargepoint.data["config"]["connection_module"]["config"]["external_openwb"]["ip_address"], no_json=True)
                except Exception as e:
                    log.MainLogger().exception("Fehler im System-Modul")
        except Exception as e:
            log.MainLogger().exception("Fehler im System-Modul")

    def set_default_values(self):
        """ ruft für jedes Modul die rekursive Funktion zur Überprüfung auf fehlende Werte auf.
        """
        try:
            # für jeden LP müssen die defaults geprüft werden
            for cp in data.data.cp_data:
                if "cp" in cp:
                    self._check_key(subdata.SubData.defaults_cp_data["cp0"].data, data.data.cp_data[cp].data)
            for cpt in data.data.cp_template_data:
                if "cpt" in cpt:
                    self._check_key(subdata.SubData.defaults_cp_template_data["cpt0"].data, data.data.cp_template_data[cpt].data)
            for pv in data.data.pv_data:
                if "pv" in pv:
                    self._check_key(subdata.SubData.defaults_pv_data["pv0"].data, data.data.pv_data[pv].data)
            for ev in data.data.ev_data:
                if "ev" in ev:
                    self._check_key(subdata.SubData.defaults_ev_data["ev0"].data, data.data.ev_data[ev].data)
            for et in data.data.ev_template_data:
                if "et" in et:
                    self._check_key(subdata.SubData.defaults_ev_template_data["et0"].data, data.data.ev_template_data[et].data)
            for ct in data.data.ev_charge_template_data:
                if "ct" in ct:
                    self._check_key(subdata.SubData.defaults_ev_charge_template_data["ct0"].data, data.data.ev_charge_template_data[ct].data)
            for counter in data.data.counter_data:
                if "counter" in counter:
                    self._check_key(subdata.SubData.defaults_counter_data["counter0"].data, data.data.counter_data[counter].data)
            for bat in data.data.bat_data:
                if "bat" in bat:
                    self._check_key(subdata.SubData.defaults_bat_data["bat0"].data, data.data.bat_data[bat].data)
            self._check_key(subdata.SubData.defaults_general_data["general"].data, data.data.general_data["general"].data)
            self._check_key(subdata.SubData.defaults_optional_data["optional"].data, data.data.optional_data["optional"].data)
            self._check_key(subdata.SubData.defaults_system_data["system"].data, data.data.system_data["system"].data)
        except Exception as e:
            log.MainLogger().exception("Fehler im System-Modul")

    def _check_key(self, default, settings):
        """ prüft, ob ein Wert, für den es einen default-Werte gäbe, gesetzt ist, sonst wird das Dictionary mit einem default-Wert gefüllt. Dictionaries werden rekursiv 
        durchgegangen, bis das Dictionary nicht weiter verschachtelt ist.
        """
        try:
            # alle Einträge des Dictionaries durchgehen
            for key in default:
                # Ist der Value des Eintrags ein Dictionary? Dann erst dieses Dictionary durchgehen.
                if isinstance(default[key], dict) == True:
                    # prüfen, ob das Dict auch in den Einstellungen angelegt ist, sonst anlegen.
                    if key not in settings:
                        settings[key] = {}
                        # Eine Verschachtelungsebene tiefer gehen.
                    self._check_key(default[key], settings[key])
                # Der Value des Eintrags ist ein Wert. Prüfen, ob dieser Key im Modul-Dictionary exisitert, sonst Key-Value-Paar anlegen.
                else:
                    if key not in settings:
                        settings[key] = default[key]
        except Exception as e:
            log.MainLogger().exception("Fehler im System-Modul")

import threading
import _thread as thread
import sys

def quit_function(fn_name):
    # print to stderr, unbuffered in Python 2.
    sys.stderr.flush() # Python 3 stderr is likely buffered.
    thread.interrupt_main() # raises KeyboardInterrupt

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