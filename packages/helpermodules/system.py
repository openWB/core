""" Modul zum Updaten der Steuerung und Triggern der externen Wbs, zu updaten."""

import logging
import os
import subprocess
import time
from pathlib import Path


from helpermodules import pub
from control import data
from modules.common import req

log = logging.getLogger(__name__)


class System:
    def __init__(self):
        """
        """
        self.data = {"cloud_backup": {"ip_address": None, "password": None, "user": None},
                     "update_in_progress": False,
                     "perform_update": False}

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
        log.info("my IP: "+new_ip)
        if new_ip != self.data["ip_address"] and new_ip != "":
            self.data["ip_address"] = new_ip
            pub.Pub().pub("openWB/set/system/ip_address", new_ip)

    def create_backup_and_send_to_cloud(self):
        cloud_backup = self.data["cloud_backup"]
        if cloud_backup["ip_address"] is not None:
            backup_filename = self.create_backup()
            with open(self._get_parent_file()/'data'/'backup'/backup_filename, 'rb') as f:
                data = f.read()
            req.get_http_session().put(
                f'{cloud_backup["ip_address"]}/public.php/webdav/{backup_filename}',
                headers={'X-Requested-With': 'XMLHttpRequest', },
                data=data,
                auth=(cloud_backup["user"], '' if cloud_backup["password"] is None else cloud_backup["password"]),
            )
            log.debug(f'Sicherung erstellt und unter {cloud_backup["ip_address"]}/public.php/webdav/'
                      f'{backup_filename} hochgeladen.')

    def create_backup(self) -> str:
        result = subprocess.run([str(self._get_parent_file() / "runs" / "backup.sh"), "1"], stdout=subprocess.PIPE)
        if result.returncode == 0:
            file_name = result.stdout.decode("utf-8").rstrip('\n')
            return file_name
        else:
            raise Exception(f'Backup-Status: {result.returncode}, Meldung: {result.stdout.decode("utf-8")}')

    def _get_parent_file(self) -> Path:
        return Path(__file__).resolve().parents[2]
