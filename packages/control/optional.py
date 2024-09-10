"""Optionale Module
"""
from dataclasses import dataclass, field
import logging
from math import ceil  # Aufrunden
import threading
from typing import Dict, List

from dataclass_utils.factories import empty_dict_factory
from helpermodules import hardware_configuration
from helpermodules.constants import NO_ERROR
from helpermodules.pub import Pub
from helpermodules.timecheck import create_unix_timestamp_current_full_hour
from helpermodules.utils import thread_handler
from modules.common.configurable_tariff import ConfigurableElectricityTariff
from modules.display_themes.cards.config import CardsDisplayTheme

log = logging.getLogger(__name__)


@dataclass
class EtGet:
    fault_state: int = 0
    fault_str: str = NO_ERROR
    prices: Dict = field(default_factory=empty_dict_factory)


def get_factory() -> EtGet:
    return EtGet()


@dataclass
class Et:
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
    theme: CardsDisplayTheme = CardsDisplayTheme()


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
    dc_charging: bool = False


class Optional:
    def __init__(self):
        try:
            self.data = OptionalData()
            self.et_module: ConfigurableElectricityTariff = None
            self.data.dc_charging = hardware_configuration.get_hardware_configuration_setting("dc_charging")
            Pub().pub("openWB/optional/dc_charging", self.data.dc_charging)
        except Exception:
            log.exception("Fehler im Optional-Modul")

    def et_provider_available(self) -> bool:
        return self.et_module is not None and self.data.et.get.fault_state != 2

    def et_price_lower_than_limit(self, max_price: float):
        """ prüft, ob der aktuelle Strompreis unter der festgelegten Preisgrenze liegt.

        Return
        ------
        True: Preis liegt darunter
        False: Preis liegt darüber
        """
        try:
            if self.et_get_current_price() <= max_price:
                return True
            else:
                return False
        except KeyError:
            log.exception("Fehler beim strompreisbasierten Laden")
            self.et_get_prices()
        except Exception:
            log.exception("Fehler im Optional-Modul")
            return False

    def et_get_current_price(self):
        return self.data.et.get.prices[str(create_unix_timestamp_current_full_hour())]

    def et_get_loading_hours(self, duration: float, remaining_time: float) -> List[int]:
        """
        Parameter
        ---------
        duration: float
            benötigte Ladezeit

        Return
        ------
        list: Key des Dictionary (Unix-Sekunden der günstigen Stunden)
        """
        try:
            prices = self.data.et.get.prices
            prices_in_scheduled_time = {}
            i = 0
            for timestamp, price in prices.items():
                if i < ceil((duration+remaining_time)/3600):
                    prices_in_scheduled_time.update({timestamp: price})
                    i += 1
                else:
                    break
            ordered = sorted(prices_in_scheduled_time.items(), key=lambda x: x[1])
            return [int(i[0]) for i in ordered][:ceil(duration/3600)]
        except Exception:
            log.exception("Fehler im Optional-Modul")
            return []

    def et_get_prices(self):
        try:
            if self.et_module:
                thread_handler(threading.Thread(target=self.et_module.update, args=(), name="electricity tariff"))
            else:
                # Wenn kein Modul konfiguriert ist, Fehlerstatus zurücksetzen.
                if self.data.et.get.fault_state != 0 or self.data.et.get.fault_str != NO_ERROR:
                    Pub().pub("openWB/set/optional/et/get/fault_state", 0)
                    Pub().pub("openWB/set/optional/et/get/fault_str", NO_ERROR)
        except Exception:
            log.exception("Fehler im Optional-Modul")
