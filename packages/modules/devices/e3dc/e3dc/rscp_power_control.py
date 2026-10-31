#!/usr/bin/env python3
import logging
from typing import Optional

from e3dc import E3DC
from e3dc._rscpTags import RscpTag, RscpType

log = logging.getLogger(__name__)

# EMS_REQ_SET_POWER_MODE-Werte. Tag-Namen und Modus-Werte sind an echter Hardware verifiziert
# (openWB/core#3450).
MODE_AUTO = 0
MODE_IDLE = 1
MODE_DISCH = 2
MODE_CHRG = 3


class E3dcRscpBatControl:
    def __init__(self, ip_address: str, portal_username: str, portal_password: str, rscp_key: str) -> None:
        self.ip_address = ip_address
        self.portal_username = portal_username
        self.portal_password = portal_password
        self.rscp_key = rscp_key
        self.client: Optional[E3DC] = None

    def __connect(self) -> E3DC:
        if self.client is None:
            self.client = E3DC(E3DC.CONNECT_LOCAL,
                               username=self.portal_username,
                               password=self.portal_password,
                               ipAddress=self.ip_address,
                               key=self.rscp_key)
        return self.client

    def __set_power(self, mode: int, value_w: int) -> None:
        self.__connect().sendRequest(
            (RscpTag.EMS_REQ_SET_POWER, RscpType.Container,
             [(RscpTag.EMS_REQ_SET_POWER_MODE, RscpType.UChar8, mode),
              (RscpTag.EMS_REQ_SET_POWER_VALUE, RscpType.Int32, max(0, int(value_w)))]),
            keepAlive=True)

    def set_power_limit(self, power_limit: Optional[float]) -> None:
        if power_limit is None:
            log.debug("Keine Batteriesteuerung, Selbstregelung durch E3DC")
            self.__set_power(MODE_AUTO, 0)
        elif power_limit == 0:
            log.debug("Aktive Batteriesteuerung. Batterie wird auf Stop gesetzt und nicht entladen")
            self.__set_power(MODE_IDLE, 0)
        elif power_limit < 0:
            log.debug(f"Aktive Batteriesteuerung. Batterie wird mit {abs(power_limit)} W "
                      "entladen für den Hausverbrauch")
            self.__set_power(MODE_DISCH, abs(power_limit))
        else:
            log.debug(f"Aktive Batteriesteuerung. Batterie wird mit {power_limit} W geladen")
            self.__set_power(MODE_CHRG, power_limit)
