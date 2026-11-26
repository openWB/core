from typing import Optional

from control import data
from control.ocpp.helper import get_chargebox_id, is_ocpp_stop_active
from helpermodules import timecheck
from helpermodules.pub import Pub


class ChargepointOcppRfidMixin:
    """OCPP-Autorisierung, RFID-Stops und zielgebundene RemoteStart-Tags."""

    def _is_ocpp_rfid_active(self) -> bool:
        return bool(data.data.optional_data.data.ocpp.config.active and get_chargebox_id(self))

    def _is_ocpp_rfid_assignment_blocked(self) -> bool:
        """OCPP-Sperren fuer neue RFID-Zuordnungen, nicht fuer Transaktionsstopps."""
        return self._is_ocpp_rfid_active() and (
            is_ocpp_stop_active(self.data.get.ocpp)
            or not all(self.data.get.ocpp.availability)
        )

    def _is_ocpp_rfid_transaction(self) -> bool:
        """RFID-Scans dieser Transaktion werden vom OCPP-Ablauf verarbeitet."""
        return bool(data.data.optional_data.data.ocpp.config.active
                    and data.data.optional_data.data.rfid.active
                    and get_chargebox_id(self)
                    and self.data.get.ocpp.transaction_id is not None)

    def _discard_ocpp_rfid_authorization(self) -> None:
        data.data.ocpp_client.discard_rfid_authorization(get_chargebox_id(self))

    def _reset_ocpp_remote_start(self) -> None:
        self.data.get.ocpp.remote_start = False
        Pub().pub(f"openWB/set/chargepoint/{self.num}/get/ocpp/remote_start", False)

    def _reset_ocpp_rfid_flow(self) -> None:
        if self.data.get.ocpp.authorization_flow_status != "start_unconfirmed":
            self.data.get.ocpp.authorization_flow_status = None
            Pub().pub(f"openWB/set/chargepoint/{self.num}/get/ocpp/authorization_flow_status", None)

    def _get_ocpp_rfid_flow(self) -> Optional[str]:
        return self.data.get.ocpp.authorization_flow_status if self._is_ocpp_rfid_active() else None

    def _validate_ocpp_rfid(self) -> bool:
        """True: OCPP hat den Scan bereinigt oder haelt ihn fuer die Transaktion vor."""
        if self.data.get.ocpp.remote_start:
            # Auch update_ev() arbeitet auf Kopien: nur im Regelzyklus bereinigen.
            if data.data.cp_data.get(f"cp{self.num}") is not self:
                return True
            if (not data.data.optional_data.data.ocpp.config.active or not get_chargebox_id(self)
                    or (self.data.set.rfid is not None and self.data.set.rfid != self.data.get.rfid)):
                self._clear_scanned_rfid()
                return True
        if (self._is_ocpp_rfid_active() and not all(self.data.get.ocpp.availability)
                and self.data.get.ocpp.transaction_id is None):
            if not self.data.get.ocpp.remote_start and self.find_duo_partner() is not None:
                # Lokalen Scan durch die Duo-Verteilung am verfuegbaren Partner behalten.
                return False
            # Auch beim Aufruf aus update_ev() keine Wartephase fuer gesperrte Ladepunkte beginnen.
            self._clear_scanned_rfid()
            return True
        if self._is_ocpp_rfid_transaction():
            # Wie beim Einzel-LP den Scan bis zur OCPP-Antwort behalten.
            # Weder die bestehende Zuordnung aendern noch den Duo-Partner bereinigen.
            if data.data.cp_data.get(f"cp{self.num}") is not self:
                return True
            if not self._is_rfid_allowed(self.data.get.rfid):
                rfid = self.data.get.rfid
                self._clear_scanned_rfid()
                self.set_state_and_log(
                    f"Der ID-Tag {rfid} ist hier keinem Ladepunkt-Profil oder Fahrzeug zugeordnet.")
            return True
        return False

    def _wait_for_ocpp_rfid_authorization(self) -> bool:
        """Laufende OCPP-Autorisierung vor der normalen RFID-Wartefrist behandeln."""
        if not self._is_ocpp_rfid_active():
            return False
        if self.data.get.ocpp.transaction_id is not None:
            # Scan waehrend einer Transaktion wird im OCPP-RFID-Ablauf behandelt.
            return True
        if self.data.get.ocpp.authorization_flow_status != "init":
            return False
        # Die noch laufende OCPP-Autorisierung darf den Tag nicht loeschen.
        if self.data.get.rfid_timestamp is None:
            self.data.get.rfid_timestamp = timecheck.create_timestamp()
            Pub().pub(f"openWB/set/chargepoint/{self.num}/get/rfid_timestamp", self.data.get.rfid_timestamp)
        elif not timecheck.check_timestamp(self.data.get.rfid_timestamp, 300):
            self._clear_scanned_rfid()
            self.set_state_and_log("OCPP-RFID-Autorisierung nach 5 Minuten abgebrochen.")
        return True

    def _clear_scanned_rfid(self) -> None:
        """Entfernt einen abgearbeiteten Scan inklusive OCPP-Antwort."""
        remote_start = bool(self.data.get.ocpp.remote_start)
        if remote_start:
            self._reset_ocpp_remote_start()
        self._discard_ocpp_rfid_authorization()
        self.data.get.rfid = None
        Pub().pub(f"openWB/set/chargepoint/{self.num}/get/rfid", None)
        self.data.get.rfid_timestamp = None
        Pub().pub(f"openWB/set/chargepoint/{self.num}/get/rfid_timestamp", None)
        flow_status = self.data.get.ocpp.authorization_flow_status
        if (flow_status != "start_unconfirmed" and
                (not data.data.optional_data.data.rfid.active or flow_status not in (
                    "start_pending", "start_starting", "start_authorizing", "start_rejected", "start_error"))):
            self.data.get.ocpp.authorization_flow_status = None
            Pub().pub(f"openWB/set/chargepoint/{self.num}/get/ocpp/authorization_flow_status", None)
        if not remote_start:
            self.chargepoint_module.clear_rfid()

    def _process_ocpp_rfid(self) -> None:
        """Verarbeitet OCPP-Autorisierungen und RFID-Stops genau einmal pro Scan."""
        if self._rfid_stop_result is not None:
            self.set_state_and_log(
                "OCPP-Transaktionsstopp per RFID bestätigt."
                if self._rfid_stop_result else
                "OCPP-Transaktionsstopp per RFID fehlgeschlagen oder abgelehnt.")
            self._rfid_stop_result = None

        if self.data.get.ocpp.previous_chargebox_id:
            return
        chargebox_id = get_chargebox_id(self)
        ocpp_active = data.data.optional_data.data.ocpp.config.active and chargebox_id
        rfid_active = data.data.optional_data.data.rfid.active
        if not ocpp_active or not rfid_active:
            data.data.ocpp_client.discard_rfid_authorization(chargebox_id)
            if self.data.get.ocpp.authorization_flow_status == "init":
                self.data.get.ocpp.authorization_flow_status = None
                Pub().pub(
                    f"openWB/set/chargepoint/{self.num}/get/ocpp/authorization_flow_status", None)
            return

        # Verspaetete Kopien eines Freischaltungsscans vor Stop/Authorize verwerfen.
        # Die normale RFID-Validierung folgt erst nach der OCPP-Verarbeitung.
        if self.data.get.rfid is not None and not self.data.get.ocpp.remote_start:
            # Nur den eigenen Abschluss vergleichen: Der Nicht-OCPP-Partner
            # kann denselben Scan schon bereinigt haben, waehrend hier noch
            # eine unabhaengige Transaktions-Autorisierung aussteht.
            if self._discard_processed_rfid():
                return

        if (not all(self.data.get.ocpp.availability)
                and self.data.get.ocpp.transaction_id is None):
            # Lokale Duo-Scans erst in _validate_rfid() verteilen, ohne den Leser
            # vorzeitig zu quittieren. RemoteStart bleibt an diesen LP gebunden.
            if (self.data.get.rfid is not None and
                    (self.data.get.ocpp.remote_start or self.find_duo_partner() is None)):
                self._clear_scanned_rfid()
            return

        # Eine eindeutige Duo-Freischaltung hat Vorrang vor RFID-Stop/Authorize-only.
        # Bei RemoteStart steht das Ziel bereits fest.
        if self.data.get.rfid is not None and not self.data.get.ocpp.remote_start:
            partner_num = self.find_duo_partner()
            if partner_num is not None:
                partner = data.data.cp_data[f"cp{partner_num}"]
                target = self._rfid_target(partner, self.data.get.rfid_timestamp)
                if target is not self and (target is not None or self.data.get.ocpp.transaction_id is None):
                    # Den Scan nur am Freischaltungsziel verarbeiten. Ohne Ziel
                    # bleiben Autorisierung und Stop laufender Transaktionen moeglich.
                    return

        data.data.ocpp_client.finish_rfid_authorization(
            chargebox_id,
            self,
        )
        if self.data.get.rfid is not None:
            rfid = self.data.get.rfid
            response = self.data.get.ocpp.authorization_flow_status
            valid_tag = self._is_rfid_allowed(rfid)
            transaction_active = self.data.get.ocpp.transaction_id is not None

            if valid_tag and transaction_active and response is None and rfid == (
                    self.data.get.ocpp.transaction_id_tag or self.data.set.rfid):
                # Erneuter Scan des Transaktions-Tags fordert einen RFID-Stop an.
                # Am Partner ohne Transaktion darf er nicht als Freischaltung warten.
                timestamp = self.data.get.rfid_timestamp
                partner_num = self.find_duo_partner()
                partner = data.data.cp_data.get(f"cp{partner_num}") if partner_num is not None else None
                for cp in (self, partner):
                    if (cp is None or cp.data.get.ocpp.remote_start or
                            (cp is not self and cp._is_ocpp_rfid_transaction())):
                        continue
                    if (timestamp is not None and
                            (cp.data.set.rfid_timestamp is None or timestamp > cp.data.set.rfid_timestamp)):
                        cp.data.set.rfid_timestamp = timestamp
                    if (cp is not self and cp.data.get.rfid == rfid and
                            cp.data.get.rfid_timestamp == timestamp):
                        cp._discard_ocpp_rfid_authorization()
                        if cp.data.get.ocpp.authorization_flow_status in ("init", "accepted", "rejected"):
                            cp._reset_ocpp_rfid_flow()
                        # Nur Software-Kopie bereinigen; den gemeinsamen Leser
                        # quittiert anschliessend der stoppende Ladepunkt einmal.
                        cp.data.get.rfid = None
                        cp.data.get.rfid_timestamp = None
                        Pub().pub(f"openWB/set/chargepoint/{cp.num}/get/rfid", None)
                        Pub().pub(f"openWB/set/chargepoint/{cp.num}/get/rfid_timestamp", None)
                # Sofort verbrauchen: Im nächsten Update darf kein zweiter Stop erfolgen.
                self._clear_scanned_rfid()
                future = data.data.ocpp_client.request_stop(
                    chargebox_id=get_chargebox_id(self),
                    imported=self.data.get.imported,
                    id_tag=rfid,
                    reason="Local",
                    authorize_stop=True,
                )
                if future is not None:
                    def on_stop_done(completed_future):
                        try:
                            self._rfid_stop_result = bool(completed_future.result())
                        except Exception:
                            self._rfid_stop_result = False
                    future.add_done_callback(on_stop_done)
                self.set_state_and_log("OCPP-Transaktionsstopp per RFID angefragt.")
            else:
                # Authorize-only vor dem Anstecken oder mit einem anderen Tag
                # während einer Transaktion. Nie während des Pending erneut senden.
                if (valid_tag and response is None and
                        (transaction_active or
                         (not self.data.get.plug_state and
                          self.data.get.rfid_timestamp is None))):
                    data.data.ocpp_client.authorize_for_rfid(
                        chargebox_id=get_chargebox_id(self),
                        id_tag=rfid,
                    )
                    response = self.data.get.ocpp.authorization_flow_status

                if response == "rejected":
                    self._clear_scanned_rfid()
                    self.set_state_and_log(f"ID-Tag {rfid} wurde vom OCPP-Server abgelehnt.")
                elif response == "accepted":
                    self.set_state_and_log(f"ID-Tag {rfid} wurde vom OCPP-Server akzeptiert.")
                    if transaction_active:
                        # Kein Austausch des aktuellen Transaktions-Tags!
                        self._clear_scanned_rfid()
                    else:
                        self.data.get.ocpp.authorization_flow_status = None
                        Pub().pub(
                            f"openWB/set/chargepoint/{self.num}/get/ocpp/authorization_flow_status", None)
