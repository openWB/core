import logging
from typing import Optional

from control import data
from control.chargepoint.chargepoint_data import ChargepointProtocol
from helpermodules.pub import Pub
from helpermodules import timecheck

log = logging.getLogger(__name__)


class ChargepointRfidMixin:
    def _link_rfid_to_cp(self: ChargepointProtocol) -> None:
        """ Wenn der Tag einem EV zugeordnet worden ist, wird der Tag unter set/rfid abgelegt und muss der Timer
        zurückgesetzt werden.
        """
        rfid = self.data.get.rfid
        cp2_num = self.find_duo_partner()
        # Tag wird diesem LP der Duo zugewiesen oder es ist keine Duo
        if ((cp2_num is not None and
                # EV am anderen Ladepunkt, am eigenen wurde zuerst angesteckt
             ((data.data.cp_data[f"cp{cp2_num}"].data.get.plug_state and
               timecheck.get_difference(self.data.set.plug_time,
                                        data.data.cp_data[f"cp{cp2_num}"].data.set.plug_time) < 0) or
              # kein EV am anderen Duo-Ladepunkt
              data.data.cp_data[f"cp{cp2_num  }"].data.get.plug_state is False)) or
                # keine Duo
                cp2_num is None):
            self.data.set.rfid = rfid
            Pub().pub("openWB/chargepoint/"+str(self.num)+"/set/rfid", rfid)
            self.chargepoint_module.clear_rfid()

        self.data.get.rfid = None
        Pub().pub("openWB/chargepoint/"+str(self.num)+"/get/rfid", None)
        self.data.get.rfid_timestamp = None
        Pub().pub(f"openWB/set/chargepoint/{self.num}/get/rfid_timestamp", None)

    def _validate_rfid(self) -> None:
        """Prüft, dass der Tag an diesem Ladepunkt gültig ist und  dass dieser innerhalb von 5 Minuten einem EV
        zugeordnet wird.
        """
        msg = ""
        if self.data.get.rfid is not None:
            if data.data.optional_data.data.rfid.active:
                if (self.data.set.log.imported_at_plugtime == 0 or
                        self.data.set.log.imported_at_plugtime == self.data.get.imported):
                    rfid = self.data.get.rfid
                    if self.data.get.rfid_timestamp is None:
                        self.data.get.rfid_timestamp = timecheck.create_timestamp()
                        Pub().pub(f"openWB/set/chargepoint/{self.num}/get/rfid_timestamp",
                                  self.data.get.rfid_timestamp)
                        return
                    else:
                        if (timecheck.check_timestamp(self.data.get.rfid_timestamp, 300) or
                                self.data.get.plug_state is True):
                            return
                        else:
                            self.data.get.rfid_timestamp = None
                            if rfid in self.template.data.valid_tags or len(self.template.data.valid_tags) == 0:
                                Pub().pub(f"openWB/set/chargepoint/{self.num}/get/rfid_timestamp", None)
                                msg = "Es ist in den letzten 5 Minuten kein EV angesteckt worden, dem " \
                                    f"der ID-Tag {rfid} zugeordnet werden kann. Daher wird dieser verworfen."
                            else:
                                msg = f"Der ID-Tag {rfid} ist an diesem Ladepunkt nicht gültig."
                else:
                    msg = "Nach Ladestart wird kein anderer ID-Tag akzeptiert."
            else:
                msg = "Identifikation von Fahrzeugen ist nicht aktiviert."
            self.data.get.rfid = None
            Pub().pub(f"openWB/set/chargepoint/{self.num}/get/rfid", None)
            self.chargepoint_module.clear_rfid()
            self.set_state_and_log(msg)

    def find_duo_partner(self: ChargepointProtocol) -> Optional[int]:
        try:
            # Wurde ein zweiter Ladepunkt an einer Duo konfiguriert?
            if self.data.config.type == "external_openwb" or self.data.config.type == "internal_openwb":
                for cp2 in data.data.cp_data.values():
                    if (cp2.num != self.num and
                            self.data.config.configuration["ip_address"] == cp2.data.config.configuration[
                                "ip_address"]):
                        return cp2.num
            return None
        except Exception:
            log.exception("Fehler in der allgemeinen Ladepunkt-Klasse")
            return None
