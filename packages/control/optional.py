"""Optionale Module
"""
from dataclasses import dataclass, field
import logging
from math import ceil  # Aufrunden
from typing import Dict, List

from dataclass_utils.factories import empty_dict_factory, emtpy_list_factory

log = logging.getLogger(__name__)


@dataclass
class EtGet:
    price: float = 0
    price_list: List = field(default_factory=emtpy_list_factory)


def get_factory() -> EtGet:
    return EtGet()


@dataclass
class EtConfig:
    max_price: float = 0
    provider: Dict = field(default_factory=empty_dict_factory)


def et_config_factory() -> EtConfig:
    return EtConfig()


@dataclass
class Et:
    active: bool = False
    config: EtConfig = field(default_factory=et_config_factory)
    get: EtGet = field(default_factory=get_factory)


def et_factory() -> Et:
    return Et()


@dataclass
class InternalDisplay:
    active: bool = False
    on_if_plugged_in: bool = True
    pin_active: bool = False
    pin_code: str = "0000"
    standby: int = 60
    theme: str = "cards"


def int_display_factory() -> InternalDisplay:
    return InternalDisplay()


@dataclass
class Led:
    active: bool = False


def led_factory() -> Led:
    return Led()


@dataclass
class Rfid:
    active: bool = False


def rfid_factory() -> Rfid:
    return Rfid()


@dataclass
class OptionalData:
    et: Et = field(default_factory=et_factory)
    int_display: InternalDisplay = field(default_factory=int_display_factory)
    led: Led = field(default_factory=led_factory)
    rfid: Rfid = field(default_factory=rfid_factory)


class Optional:
    def __init__(self):
        try:
            self.data = OptionalData()
        except Exception:
            log.exception("Fehler im Optional-Modul")

    def et_price_lower_than_limit(self):
        """ prüft, ob der aktuelle Strompreis unter der festgelegten Preisgrenze liegt.

        Return
        ------
        True: Preis liegt darunter
        False: Preis liegt darüber
        """
        try:
            if self.data.et.get.price <= self.data.et.config.max_price:
                return True
            else:
                return False
        except Exception:
            self.et_get_prices()
            log.exception("Fehler im Optional-Modul")
            return False

    def et_get_loading_hours(self, duration):
        """ geht die Preise der nächsten 24h durch und liefert eine Liste der Uhrzeiten, zu denen geladen werden soll

        Parameter
        ---------
        duration: float
            benötigte Ladezeit

        Return
        ------
        list: Key des Dictionary (Unix-Sekunden der günstigen Stunden)
        """
        try:
            price_list = self.data.et.get.price_list
            return [
                i[0] for i in sorted(price_list, key=lambda x: x[1])
                [:ceil(duration)]
            ]
        except Exception:
            self.et_get_prices()
            log.exception("Fehler im Optional-Modul")
            return []

    def et_get_prices(self):
        try:
            if self.data.et.active:
                # if self.data["et"]["config"]["provider"]["provider"] == "awattar":
                #     awattargetprices.update_pricedata(
                #         self.data["et"]["config"]["provider"]["country"], 0)
                # elif self.data["et"]["config"]["provider"]["provider"] == "tibber":
                #     tibbergetprices.update_pricedata(
                #         self.data["et"]["config"]["provider"]["token"], self.data["et"]["config"]["provider"]["id"])
                # else:
                log.error("Unbekannter Et-Provider.")
        except Exception:
            log.exception("Fehler im Optional-Modul")
