""" Modul zum Updaten der Steuerung und Triggern der externen Wbs, zu updaten."""

import logging
import os
import subprocess
import threading
import time
from pathlib import Path
from typing import Optional


from helpermodules import pub
from control import data
from helpermodules.utils import thread_handler
from helpermodules.utils.run_command import run_command
from modules.common.configurable_backup_cloud import ConfigurableBackupCloud

log = logging.getLogger(__name__)


class System:
    def __init__(self):
        """
        """
        self.data = {"update_in_progress": False,
                     "perform_update": False,
                     "backup_cloud": {}}
        self.backup_cloud: Optional[ConfigurableBackupCloud] = None

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
            # run_command([str(Path(__file__).resolve().parents[2]/"runs"/"update_self.sh"), train])
            run_command(str(Path(__file__).resolve().parents[2]/"runs"/"atreboot.sh"), process_exception=True)
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
        log.info("my IP: "+new_ip)
        if new_ip != self.data["ip_address"] and new_ip != "":
            self.data["ip_address"] = new_ip
            pub.Pub().pub("openWB/set/system/ip_address", new_ip)

    def thread_backup_and_send_to_cloud(self):
        def create():
            try:
                self.create_backup_and_send_to_cloud()
            except Exception as e:
                log.exception(f"Error in cloud backup: {e}")
        thread_handler(threading.Thread(target=create, args=(), name="cloud backup"))

    def create_backup_and_send_to_cloud(self):
        if self.backup_cloud is not None:
            backup_filename = self.create_backup()
            with open(self._get_parent_file()/'data'/'backup'/backup_filename, 'rb') as f:
                data = f.read()
            self.backup_cloud.update(backup_filename, data)
            log.debug('Nächtliche Sicherung erstellt und hochgeladen.')

    def create_backup(self) -> str:
        try:
            result = run_command([str(self._get_parent_file() / "runs" / "backup.sh"), "1"])
            file_name = result.rstrip('\n')
            return file_name
        except subprocess.CalledProcessError as e:
            log.debug(e.stdout)
            raise Exception(f'Backup-Status: {e.returncode}, Meldung: {e.stderr}')

    def _get_parent_file(self) -> Path:
        return Path(__file__).resolve().parents[2]
