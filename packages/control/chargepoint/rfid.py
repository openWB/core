import logging
from fnmatch import fnmatch
from typing import Optional

from control import data
from control.chargepoint.chargepoint_data import ChargepointProtocol
from helpermodules.pub import Pub
from helpermodules import timecheck

log = logging.getLogger(__name__)


class ChargepointRfidMixin:
    def _rfid_target(self: ChargepointProtocol, cp2_data, rfid_timestamp=None):
        """Nur unzugeordnete Duo-LP ohne begonnenen Ladevorgang berücksichtigen."""
        candidates = [cp for cp in (self, cp2_data)
                      if cp.data.set.rfid is None and cp.data.get.plug_state and
                      (cp.data.set.log.imported_at_plugtime == 0 or
                       cp.data.set.log.imported_at_plugtime == cp.data.get.imported)]
        if len(candidates) == 1:
            return candidates[0]
        if len(candidates) != 2:
            return None
        first, second = candidates
        t1, t2 = first.data.set.plug_time, second.data.set.plug_time
        if t1 is None or t2 is None or t1 == t2:
            return None
        # Scan vor dem Anstecken: das erste Auto bekommt den wartenden Tag,
        # auch wenn bis zur Verarbeitung bereits beide Autos eingesteckt sind.
        if rfid_timestamp is not None and max(t1, t2) > rfid_timestamp:
            return first if t1 < t2 else second
        # Wenn beim Scan beide Autos bereit stehen, das letzte wählen.
        return first if (t2 - t1) < 0 else second

    def _clear_pending_rfid(self: ChargepointProtocol, rfid: str, cp2_data=None) -> None:
        """Gemeinsamen Scan einmal quittieren, verbindliche Zuordnungen behalten."""
        for cp in (self, cp2_data):
            if cp is not None and cp.data.get.rfid == rfid:
                cp.data.get.rfid = None
                Pub().pub(f"openWB/set/chargepoint/{cp.num}/get/rfid", None)
                cp.data.get.rfid_timestamp = None
                Pub().pub(f"openWB/set/chargepoint/{cp.num}/get/rfid_timestamp", None)
        self.chargepoint_module.clear_rfid()

    def _link_rfid_to_cp(self: ChargepointProtocol) -> None:
        """ tested
        Wenn der Tag einem EV zugeordnet worden ist, wird der Tag unter set/rfid abgelegt und muss der Timer
        zurückgesetzt werden.
        """
        rfid = self.data.get.rfid
        if rfid is None:
            return
        # Duo-Zuordnung, falls Duo Partner vorhanden ist.
        cp2_num = self.find_duo_partner()
        cp2_data = data.data.cp_data[f"cp{cp2_num}"] if cp2_num is not None else None
        if cp2_data is not None:
            target = self._rfid_target(cp2_data, self.data.get.rfid_timestamp)
            if target is not None:
                target.data.set.rfid = rfid
                self._clear_pending_rfid(rfid, cp2_data)
            return

        # Einzel-LP:
        self.data.set.rfid = rfid
        self.chargepoint_module.clear_rfid()

        self.data.get.rfid = None
        Pub().pub("openWB/chargepoint/"+str(self.num)+"/get/rfid", None)
        self.data.get.rfid_timestamp = None
        Pub().pub(f"openWB/set/chargepoint/{self.num}/get/rfid_timestamp", None)

    def _validate_rfid(self) -> None:
        """Prüft, dass der Tag an diesem Ladepunkt gültig ist und dass dieser innerhalb von 5 Minuten einem EV
        zugeordnet wird.
        """
        msg = ""
        if self.data.get.rfid is not None:
            rfid = self.data.get.rfid
            cp2_num = self.find_duo_partner()
            cp2_data = data.data.cp_data.get(f"cp{cp2_num}") if cp2_num is not None else None
            # Duo-LP:
            if cp2_data is not None:
                # update_ev() arbeitet im Hintergrund auf einer Kopie. Dort keine
                # Scans quittieren oder den globalen Partner verändern.
                if data.data.cp_data.get(f"cp{self.num}") is not self:
                    return

                # Beide Ladepunkte sind bereits zugeordnet oder laden. Es wird kein weiterer ID-Tag akzeptiert.
                if all(cp.data.set.rfid is not None or cp.data.get.charge_state for cp in (self, cp2_data)):
                    self._clear_pending_rfid(rfid, cp2_data)
                    for cp in (self, cp2_data):
                        cp.set_state_and_log("Beide Ladepunkte sind bereits zugeordnet oder laden."
                                             " Es wird kein weiterer ID-Tag akzeptiert.")
                    return
                allowed_cps = [cp for cp in (self, cp2_data)
                               if cp.data.set.rfid is None and
                               (not cp.data.get.plug_state or cp.data.set.log.imported_at_plugtime == 0 or
                                cp.data.set.log.imported_at_plugtime == cp.data.get.imported)]
                # Beide Eingänge verwenden den frühesten vorhandenen Scanzeitpunkt.
                timestamps = [cp.data.get.rfid_timestamp for cp in (self, cp2_data)
                              if cp.data.get.rfid is not None and cp.data.get.rfid_timestamp is not None]
                timestamp = min(timestamps) if timestamps else timecheck.create_timestamp()
                target = self._rfid_target(cp2_data, timestamp)
                if target is not None:
                    allowed_cps = [target]

                # Ist Liste leer -> Abbrechen
                if not allowed_cps:
                    self._clear_pending_rfid(rfid, cp2_data)
                    return
                if not data.data.optional_data.data.rfid.active:
                    msg = "Identifikation von Fahrzeugen ist nicht aktiviert."

                # Der Tag muss an einem erlaubten Ladepunkt oder einem EV gültig sein.
                elif not any(any(fnmatch(rfid, tag_id) for tag_id in cp.template.data.valid_tags) or
                             (not cp.data.set.manual_lock and
                              any(rfid in v.data.tag_id for v in data.data.ev_data.values()))
                             for cp in allowed_cps):
                    msg = f"Der ID-Tag {rfid} ist an diesem Ladepunkt nicht gültig."
                # Timeout nur dann, wenn inzwischen kein geeignetes Auto steckt.
                elif not timecheck.check_timestamp(timestamp, 300) and target is None:
                    for cp in allowed_cps:
                        if not cp.data.get.plug_state and cp.data.get.rfid == rfid:
                            if cp.template.data.disable_after_unplug:
                                cp.data.set.manual_lock = True
                            if cp.data.set.charging_ev_data.charge_template.data.load_default:
                                cp.data.config.ev = 0
                    msg = ("Es ist in den letzten 5 Minuten kein EV angesteckt worden, dem "
                           f"der ID-Tag {rfid} zugeordnet werden kann. Daher wird dieser verworfen.")
                # Ablehnung und Timeout haben denselben Abschluss.
                if msg:
                    self._clear_pending_rfid(rfid, cp2_data)
                    for cp in allowed_cps:
                        cp.set_state_and_log(msg)
                    return

                # Gültigen Scan nur an den erlaubten LP behalten. Am Partner
                # gegebenenfalls denselben vorläufigen Scan entfernen.
                for cp in (self, cp2_data):
                    if cp in allowed_cps and cp.data.get.rfid in (None, rfid):
                        pending_tag, pending_timestamp = rfid, timestamp
                    elif cp.data.get.rfid == rfid:
                        pending_tag, pending_timestamp = None, None
                    else:
                        continue

                    cp.data.get.rfid = pending_tag
                    Pub().pub(f"openWB/set/chargepoint/{cp.num}/get/rfid", pending_tag)
                    cp.data.get.rfid_timestamp = pending_timestamp
                    Pub().pub(f"openWB/set/chargepoint/{cp.num}/get/rfid_timestamp", pending_timestamp)
                    if pending_tag is not None and not cp.data.get.plug_state:
                        cp.set_state_and_log("Wenn nach dem Scannen nicht innerhalb von 5 Minuten ein Auto"
                                             " angesteckt wird, wird der ID-Tag verworfen.")
                return
            # Einzel-LP:
            if data.data.optional_data.data.rfid.active:
                if (rfid in self.template.data.valid_tags or
                        any(rfid in v.data.tag_id for v in data.data.ev_data.values())):
                    if (self.data.set.log.imported_at_plugtime == 0 or
                            self.data.set.log.imported_at_plugtime == self.data.get.imported):
                        if self.data.get.rfid_timestamp is None:
                            self.data.get.rfid_timestamp = timecheck.create_timestamp()
                            Pub().pub(f"openWB/set/chargepoint/{self.num}/get/rfid_timestamp",
                                      self.data.get.rfid_timestamp)
                            return
                        else:
                            if timecheck.check_timestamp(self.data.get.rfid_timestamp, 300):
                                self.set_state_and_log("Wenn nach dem Scannen nicht innerhalb von 5 Minuten ein Auto"
                                                       " angesteckt wird, wird der ID-Tag verworfen.")
                                return
                            elif self.data.get.plug_state is True:
                                return
                            else:
                                self.data.get.rfid_timestamp = None
                                if self.template.data.disable_after_unplug:
                                    self.data.set.manual_lock = True
                                if self.data.set.charging_ev_data.charge_template.data.load_default:
                                    self.data.config.ev = 0
                                Pub().pub(f"openWB/set/chargepoint/{self.num}/get/rfid_timestamp", None)
                                msg = ("Es ist in den letzten 5 Minuten kein EV angesteckt worden, dem "
                                       f"der ID-Tag {rfid} zugeordnet werden kann. Daher wird dieser verworfen.")
                    else:
                        msg = "Nach Ladestart wird kein anderer ID-Tag akzeptiert."
                else:
                    msg = f"Der ID-Tag {rfid} ist an diesem Ladepunkt nicht gültig."
            else:
                msg = "Identifikation von Fahrzeugen ist nicht aktiviert."
            self.data.get.rfid = None
            Pub().pub(f"openWB/set/chargepoint/{self.num}/get/rfid", None)
            self.data.get.rfid_timestamp = None
            Pub().pub(f"openWB/set/chargepoint/{self.num}/get/rfid_timestamp", None)
            self.chargepoint_module.clear_rfid()
            self.set_state_and_log(msg)

    def find_duo_partner(self: ChargepointProtocol) -> Optional[int]:
        try:
            # Wurde ein zweiter Ladepunkt an einer Duo konfiguriert?
            if self.data.config.type == "external_openwb" or self.data.config.type == "internal_openwb":
                for cp2 in data.data.cp_data.values():
                    if (cp2.num != self.num and
                            cp2.data.config.type in ("internal_openwb", "external_openwb") and
                            self.data.config.configuration["ip_address"] == cp2.data.config.configuration[
                                "ip_address"]):
                        return cp2.num
            return None
        except Exception:
            log.exception("Fehler in der allgemeinen Ladepunkt-Klasse")
            return None
