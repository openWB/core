# UpdateConfig startet dieses Modul als eigenen Hintergrundprozess. Eine globale
# Dateisperre verhindert parallele Worker. Nach dem Einlesen des MQTT-Zustands
# laufen fehlende upgrade_file_operation_<version>() synchron in Versionsreihenfolge.
# Erst nach normaler Rückkehr wird die Version gespeichert; bei einer weitergegebenen
# Exception endet der Lauf. Beim nächsten Worker-Start werden abgeschlossene Versionen
# übersprungen und die fehlgeschlagene Migration erneut versucht (kein Rollback).
# Migrationen müssen deshalb nach Teilabbrüchen wiederholbar sein. Neue Migrationen
# hier ergänzen und FILE_OPERATION_VERSION anheben.
# log_data_ready betrifft nur Migration 0, nicht den Abschluss aller Migrationen.

import copy
import fcntl
import json
import logging
from pathlib import Path

from paho.mqtt.client import Client as MqttClient, MQTTMessage

from helpermodules import logger
from helpermodules.broker import BrokerClient
from helpermodules.measurement_logging.generate_totals_subprocess import generate_totals
from helpermodules.messaging import MessageType, pub_system_message
from helpermodules.pub import Pub
from helpermodules.utils.topic_parser import decode_payload


log = logging.getLogger(__name__)
LOCK_FILE = Path(__file__).resolve().parents[2] / "data" / "filesystem_migrations.lock"


class FilesystemMigrations:
    FILE_OPERATION_VERSION = 0

    def __init__(self) -> None:
        self.all_received_topics = {}

    def on_connect(self, client: MqttClient, userdata, flags: dict, rc: int):
        client.subscribe("openWB/#", 2)

    def on_message(self, client: MqttClient, userdata, msg: MQTTMessage):
        self.all_received_topics.update({msg.topic: msg.payload})

    def _update_topic(self, topic: str, payload) -> None:
        publish_info = Pub().publisher.client.publish(topic, json.dumps(payload), qos=1, retain=True)
        publish_info.wait_for_publish(timeout=10)
        if not publish_info.is_published():
            raise TimeoutError(f"Topic '{topic}' konnte nicht gespeichert werden.")
        self.all_received_topics[topic] = copy.deepcopy(payload)

    def update_filesystem(self) -> None:
        """Liest den aktuellen Broker-Zustand im Migrationsprozess ein."""
        broker = BrokerClient("filesystem-migrations", self.on_connect, self.on_message)
        try:
            broker.start_finite_loop()
        finally:
            broker.disconnect()
        self.__solve_breaking_changes_filesystem()

    def __solve_breaking_changes_filesystem(self) -> None:
        """Führt fehlende Migrationen synchron aus und markiert nur erfolgreiche Abschlüsse."""
        file_operation_version = decode_payload(self.all_received_topics.get("openWB/system/file_operation_version"))
        if file_operation_version is None:
            # Neues Topic (z.B. bei Upgrade von älteren Versionen): alle File-Operation-Upgrades ausführen.
            file_operation_version = []
            self._update_topic("openWB/system/file_operation_version", file_operation_version)

        log.debug(f"current file operation version: {file_operation_version}")
        log.debug(f"target file operation version: {self.FILE_OPERATION_VERSION}")
        for version in list(range(self.FILE_OPERATION_VERSION+1)):
            operation_required = version not in file_operation_version
            if version == 0:
                # Alte Installationen haben Version 0 schon beim Prozessstart eingetragen.
                log_totals_generation_finished = decode_payload(
                    self.all_received_topics.get("openWB/system/log_data_ready"))
                operation_required = operation_required or log_totals_generation_finished is not True

            if operation_required:
                log.info("Dateisystem-Migration %s wird ausgeführt.", version)
                getattr(self, f"upgrade_file_operation_{version}")()
                self._append_file_operation_version(version)

    def upgrade_file_operation_0(self) -> None:
        """Generiere die Totals-Summen für Tage und Monate."""

        self._update_topic("openWB/system/log_data_ready", False)
        generate_totals()
        self.all_received_topics["openWB/system/log_data_ready"] = True

    def _append_file_operation_version(self, version: int) -> None:
        file_operation_versions = list(decode_payload(
            self.all_received_topics.get("openWB/system/file_operation_version")))
        if version not in file_operation_versions:
            file_operation_versions.append(version)
            self._update_topic("openWB/system/file_operation_version", file_operation_versions)


def run_migrations() -> None:
    LOCK_FILE.parent.mkdir(parents=True, exist_ok=True)
    # Die Lock-Datei erst nach dem gesamten Migrationslauf entfernen, auch bei Fehlern.
    with LOCK_FILE.open("a") as lock_file:
        try:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            log.info("Dateisystem-Migrationen laufen bereits. Kein zweiter Lauf gestartet.")
            return

        try:
            FilesystemMigrations().update_filesystem()
        except Exception:
            log.exception("Dateisystem-Migrationen abgebrochen.")
            pub_system_message({}, "Fehler bei der Aktualisierung der Dateisystem-Daten.", MessageType.ERROR)
            raise
        finally:
            LOCK_FILE.unlink(missing_ok=True)


if __name__ == "__main__":
    logger.setup_generate_totals_logging(include_process_log=True)
    logging.basicConfig(level=logging.DEBUG, handlers=logging.getLogger("generate_totals").handlers)
    run_migrations()
