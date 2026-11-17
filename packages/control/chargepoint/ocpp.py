import logging
from typing import Tuple, Optional
from control import data
from helpermodules.pub import Pub
from control.ocpp.helper import get_chargebox_id, is_ocpp_stop_active, _get_formatted_time

from modules.common.fault_state_level import FaultStateLevel
from ocpp.v16.enums import ChargePointStatus

log = logging.getLogger(__name__)


class ChargepointOcppMixin:
    def _process_ocpp_backend_message(self) -> None:
        message = self.data.get.ocpp.backend_message
        if message is not None:
            if data.data.optional_data.data.ocpp.config.active and get_chargebox_id(self):
                self.set_state_and_log(f"OCPP: {message}")
            self.data.get.ocpp.backend_message = None
            Pub().pub(f"openWB/set/chargepoint/{self.num}/get/ocpp/backend_message", None)

    def _process_ocpp_start(self) -> None:
        """Verarbeitet OCPP-Startanforderungen und das Zurücksetzen der Startsperre."""
        chargebox_id = get_chargebox_id(self)
        rfid = self.data.set.rfid
        if self.find_duo_partner() is None or not self.data.get.plug_state:
            rfid = rfid or self.data.get.rfid
        id_tag = rfid or self.data.get.vehicle_id
        if data.data.optional_data.data.ocpp.config.active and chargebox_id:
            if (self.data.get.plug_state is False and
                    not data.data.ocpp_client.is_unlock_in_progress(chargebox_id)):
                data.data.ocpp_client.clear_start_block(chargebox_id)
            elif (self.data.get.ocpp.connected
                    and self.data.get.plug_state and id_tag
                    and not is_ocpp_stop_active(self.data.get.ocpp)
                    and self.data.get.ocpp.authorization_flow_status not in (
                        "init", "start_pending", "start_starting", "start_authorizing", "start_unconfirmed"
                    )):
                data.data.ocpp_client.request_start(
                    chargebox_id=chargebox_id,
                    connector_id=1,
                    id_tag=id_tag,
                    imported=self.data.get.imported,
                )
            elif (self.data.get.plug_state and id_tag and
                  self.data.get.ocpp.authorization_flow_status in (
                      "init", "start_pending", "start_starting", "start_authorizing", "start_unconfirmed"
                  )):
                log.debug("OCPP %s: Start wartet auf RFID-Autorisierung/StartTransaktion", chargebox_id)
            elif self.data.get.plug_state and id_tag and not self.data.get.ocpp.connected:
                log.debug("OCPP %s: Kein Start ohne Verbindung zum OCPP-Server.", chargebox_id)

    def _publish_ocpp_state(self) -> None:
        chargebox_id = get_chargebox_id(self)
        if data.data.optional_data.data.ocpp.config.active and chargebox_id:
            # Der Client filtert unveränderte Statusmeldungen vor dem Versand.
            self.ocpp_send_status_notification()
            # Snapshots auch ohne Transaktion für Trigger aktuell halten.
            # Periodisch sendet der Client nur während einer aktiven Transaktion.
            data.data.ocpp_client.transfer_values(
                chargebox_id,
                1,
                self.data.get.ocpp.transaction_id,
                int(self.data.get.imported),
                _get_formatted_time(),
            )

    def _reset_ocpp_stop_flags_after_unplug(self) -> None:
        """Setzt OCPP-Stop-Sperren nach Abstecken und abgeschlossener Entriegelung zurück."""
        if (is_ocpp_stop_active(self.data.get.ocpp) and
                self.data.get.plug_state is False and
                not data.data.ocpp_client.is_unlock_in_progress(get_chargebox_id(self))):
            self.data.get.ocpp.remote_stop = False
            self.data.get.ocpp.unlock_stop = False
            Pub().pub(f"openWB/set/chargepoint/{self.num}/get/ocpp/unlock_stop", False)
            Pub().pub(f"openWB/set/chargepoint/{self.num}/get/ocpp/remote_stop", False)

            self.data.get.ocpp.reset = False
            Pub().pub(f"openWB/set/chargepoint/{self.num}/get/ocpp/reset", False)

            self.data.get.ocpp.rfid_stop = False
            Pub().pub(f"openWB/set/chargepoint/{self.num}/get/ocpp/rfid_stop", False)

    def _sync_ocpp_lifecycle(self) -> None:
        data.data.ocpp_client.sync_chargepoint_lifecycle(
            self.num,
            self.data.config.ocpp_chargebox_id,
            self.data.config.ocpp_chargebox_password,
            data.data.optional_data.data.ocpp.config.active,
        )

    def _is_ocpp(self) -> Tuple[bool, Optional[str]]:
        # OCPP darf Ladepunkte ohne OCPP-Konfiguration nicht beeinflussen.
        if (
            not data.data.optional_data.data.ocpp.config.active
            or not get_chargebox_id(self)
        ):
            return True, None

        state = all(self.data.get.ocpp.availability)
        if self.data.get.ocpp.previous_chargebox_id:
            if self.data.get.ocpp.authorization_flow_status == "start_unconfirmed":
                message = "Keine Ladung: OCPP-ID-Wechsel wartet auf Abstecken, da die Startbestätigung fehlt. " \
                          "Stecker abziehen und erneut verbinden."
            else:
                message = "Keine Ladung: OCPP-ID wird geändert. Bisherigen Vorgang zuerst beenden."
            state = False
        elif self.data.get.ocpp.authorization_flow_status == "start_unconfirmed":
            message = "Keine Ladung: Startbestätigung vom OCPP-Server fehlt. " \
                      "Stecker abziehen und erneut verbinden."
            state = False
        elif not self.data.get.ocpp.connected and self.data.get.ocpp.transaction_id is None:
            message = "Keine Ladung: Verbindung zum OCPP-Server fehlt."
            state = False
        elif not state:
            message = "Keine Ladung: Ladepunkt ist OCPP-seitig nicht verfügbar."
            state = False
        elif self.data.get.ocpp.reset:
            message = "Keine Ladung: Transaktion vom OCPP-Server durch ein Reset gestoppt. " \
                      "Stecker abziehen und erneut verbinden."
            state = False

        elif self.data.get.ocpp.unlock_stop:
            message = "Keine Ladung: Buchsenentriegelung angefordert. Stecker abziehen und erneut verbinden."
            state = False
        elif self.data.get.ocpp.remote_stop:
            message = "Keine Ladung: Transaktion vom OCPP-Server gestoppt. " \
                      "Stecker abziehen und erneut verbinden."
            state = False
        elif self.data.get.ocpp.rfid_stop:
            message = "Keine Ladung: Transaktion per RFID gestoppt. " \
                      "Stecker abziehen und erneut verbinden."
            state = False
        elif not self.data.get.ocpp.tag_accepted:
            message = {
                "init": "RFID-Autorisierung am OCPP-Server läuft.",
                "start_pending": "OCPP-Transaktionstart wird vorbereitet.",
                "start_authorizing": "RFID-Autorisierung am OCPP-Server läuft.",
                "start_starting": "RFID akzeptiert. OCPP-Transaktion wird gestartet.",
                "start_rejected": "Keine Ladung: OCPP Authorisierung abgelehnt.",
                "start_error": "Keine Ladung: Fehler beim OCPP-Transaktionstart.",
                "stop_pending": "Ladevorgang wird beendet.",
                "stop_error": "Server hat das Ende des Ladevorgangs nicht bestätigt.",
            }.get(self.data.get.ocpp.authorization_flow_status)
            if message is None and self.data.get.plug_state:
                if self.data.set.rfid or self.data.get.rfid or self.data.get.vehicle_id:
                    message = "Warte auf OCPP-Transaktionsfreigabe."
                else:
                    message = "Keine Ladung: RFID zur OCPP-Freigabe erforderlich."
            state = False
        else:
            message = None

        # Eine laufende Transaktion darf offline weiterladen. Den Hinweis
        # trotzdem jeden Zyklus anzeigen, auch neben bestehenden Sperrmeldungen.
        if not self.data.get.ocpp.connected and self.data.get.ocpp.transaction_id is not None:
            message = " ".join(text for text in (
                message, "OCPP: Verbindung zum Server unterbrochen.",
            ) if text)
        return state, message

    def _chargepoint_stop_ocpp(self) -> None:
        # Ocpp Stop Funktion aufrufen
        chargebox_id = get_chargebox_id(self)
        ocpp_data = self.data.get.ocpp
        transaction_exists = ocpp_data.transaction_id is not None
        start_in_progress = ocpp_data.authorization_flow_status in (
            "start_pending", "start_authorizing", "start_starting",
        )
        # hier nicht nach data.data.optional_data.data.ocpp.config.active prüfen
        # Auch ein laufender Start ohne Transaktions-ID muss abgebrochen werden können.
        if chargebox_id and (transaction_exists or start_in_progress):
            if ocpp_data.unlock_stop:
                data.data.ocpp_client.request_stop(
                    chargebox_id=chargebox_id,
                    imported=self.data.get.imported,
                    id_tag=self.data.set.rfid,
                    reason="UnlockCommand",
                )
            elif ocpp_data.remote_stop:

                data.data.ocpp_client.request_stop(
                    chargebox_id=chargebox_id,
                    imported=self.data.get.imported,
                    id_tag=self.data.set.rfid,
                    reason="Remote",
                )

            elif not self.data.get.plug_state:
                data.data.ocpp_client.request_stop(
                    chargebox_id=chargebox_id,
                    imported=self.data.get.imported,
                    id_tag=self.data.set.rfid,
                    reason="EVDisconnected",
                )

    def get_ocpp_status(self) -> ChargePointStatus:
        # Fehler haben Vorrang vor Nichtverfügbarkeit und Stop-Sperren.
        if self.data.get.fault_state >= FaultStateLevel.ERROR:
            return ChargePointStatus.faulted

        if not all(self.data.get.ocpp.availability):
            return ChargePointStatus.unavailable

        if not self.data.get.plug_state:
            return ChargePointStatus.available

        # Ein angeforderter Stop allein beendet noch keine laufende Ladung.
        # Finishing erst nach lokalem Transaktionsende, solange noch angesteckt.
        if (self.data.get.ocpp.transaction_id is None and not self.data.get.charge_state and
                is_ocpp_stop_active(self.data.get.ocpp)):
            return ChargePointStatus.finishing

        if self.data.get.ocpp.transaction_id is None:
            return ChargePointStatus.preparing

        if self.data.get.charge_state:
            return ChargePointStatus.charging

        if self.data.set.current == 0:
            return ChargePointStatus.suspended_evse

        return ChargePointStatus.suspended_ev

    def get_ocpp_status_connector_0(self) -> ChargePointStatus:
        # Connector 0 kann nur die folgenden 3 Status annehmen
        # Available, Unavailable and Faulted.

        if self.data.get.fault_state >= FaultStateLevel.ERROR:
            return ChargePointStatus.faulted

        if not self.data.get.ocpp.availability[0]:
            return ChargePointStatus.unavailable

        return ChargePointStatus.available

    def ocpp_send_status_notification(self) -> None:
        # Hier dann die StatusNotification versenden
        # im Ocpp wird sich der Status gemerkt und
        # nur neu gesendet, wenn sich der Status geändert hat
        data.data.ocpp_client.status_notification(
            chargebox_id=get_chargebox_id(self),
            connector_id=0,
            fault_state=self.data.get.fault_state,
            fault_state_str=self.data.get.fault_str,
            status=self.get_ocpp_status_connector_0()
        )
        data.data.ocpp_client.status_notification(
            chargebox_id=get_chargebox_id(self),
            connector_id=1,
            fault_state=self.data.get.fault_state,
            fault_state_str=self.data.get.fault_str,
            status=self.get_ocpp_status()
        )
