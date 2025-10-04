"""Optionale Module
"""
import logging
import datetime
from math import ceil
from threading import Thread
from typing import List

from control import data
from control.ocpp import OcppMixin
from control.optional_data import OptionalData
from helpermodules import hardware_configuration
from helpermodules.constants import NO_ERROR
from helpermodules.pub import Pub
from helpermodules.utils import thread_handler
from modules.common.configurable_tariff import ConfigurableElectricityTariff
from modules.common.configurable_monitoring import ConfigurableMonitoring
from helpermodules.timecheck import (
    create_unix_timestamp_current_quarter_hour,
    create_unix_timestamp_current_full_hour
)

log = logging.getLogger(__name__)


class Optional(OcppMixin):
    def __init__(self):
        try:
            self.data = OptionalData()
            self.et_module: ConfigurableElectricityTariff = None
            self.monitoring_module: ConfigurableMonitoring = None
            self.data.dc_charging = hardware_configuration.get_hardware_configuration_setting("dc_charging")
            Pub().pub("openWB/optional/dc_charging", self.data.dc_charging)
        except Exception:
            log.exception("Fehler im Optional-Modul")

    def monitoring_start(self):
        if self.monitoring_module is not None:
            self.monitoring_module.start_monitoring()

    def monitoring_stop(self):
        if self.mon_module is not None:
            self.mon_module.stop_monitoring()

    def et_provider_available(self) -> bool:
        return self.et_module is not None

    def et_charging_allowed(self, max_price: float):
        """ prüft, ob der aktuelle Strompreis niedriger oder gleich der festgelegten Preisgrenze ist.

        Return
        ------
        True: Preis ist gleich oder liegt darunter
        False: Preis liegt darüber
        """
        try:
            if self.et_provider_available():
                if self.et_get_current_price() <= max_price:
                    return True
                else:
                    return False
            else:
                return True
        except KeyError:
            log.exception("Fehler beim strompreisbasierten Laden")
            self.et_get_prices()
        except Exception:
            log.exception("Fehler im Optional-Modul")
            return False

    def et_get_current_price(self) -> float:
        if self.et_provider_available():
            prices = self.data.et.get.prices
            timestamp, first = next(iter(prices.items()))
            log.debug(f"first in prices list: {first} from " +
                      f"{datetime.datetime.fromtimestamp(int(timestamp)).strftime('%Y-%m-%d %H:%M')}")
            return first
        else:
            raise Exception("Kein Anbieter für strompreisbasiertes Laden konfiguriert.")

    def __calculate_price_timeslot_length(self, prices: dict) -> int:
        first_timestamps = list(prices.keys())[:2]
        return int(first_timestamps[1]) - int(first_timestamps[0])

    def et_get_loading_hours(self, duration: float, remaining_time: float) -> List[int]:
        """
        Parameter
        ---------
        duration: float
            benötigte Ladezeit
        remaining_time: float
            Restzeit bis Termin (von wo an gerechnet???)
        Return
        ------
        list: Key des Dictionary (Unix-Sekunden der günstigen Zeit-Slots)
        """
        if self.et_provider_available() is False:
            raise Exception("Kein Anbieter für strompreisbasiertes Laden konfiguriert.")
        try:
            prices = self.data.et.get.prices
            price_timeslot_seconds = self.__calculate_price_timeslot_length(prices)
            now = (
                create_unix_timestamp_current_full_hour()
                if 3600 == price_timeslot_seconds
                else create_unix_timestamp_current_quarter_hour()
            )

            log.debug(f"current full hour: "
                      f"{int(now)} {datetime.datetime.fromtimestamp(int(now)).strftime('%Y-%m-%d %H:%M')} "
                      f"Plan target Date: {int(now) + remaining_time} "
                      f"{datetime.datetime.fromtimestamp(int(now) + remaining_time).strftime('%Y-%m-%d %H:%M')}")

            prices = {
                timestamp: price
                for timestamp, price in prices.items()
                if (  # is current timeslot or futur
                    int(timestamp) >= int(now) and
                    # ends before plan target time
                    int(timestamp) + price_timeslot_seconds <= int(now) + remaining_time
                    )
            }
            log.debug(f"shrinked prices list to {len(prices)} time lots before " +
                      f"{datetime.datetime.fromtimestamp(int(now) + remaining_time).strftime('%Y-%m-%d %H:%M')}")
            ordered_by_price = sorted(prices.items(), key=lambda x: x[1])
            return sorted([int(i[0]) for i in ordered_by_price][:ceil(duration/price_timeslot_seconds)])
        except Exception:
            log.exception("Fehler im Optional-Modul")
            return []

    def et_get_prices(self):
        try:
            if self.et_module:
                thread_handler(Thread(target=self.et_module.update, args=(), name="electricity tariff"))
            else:
                # Wenn kein Modul konfiguriert ist, Fehlerstatus zurücksetzen.
                if self.data.et.get.fault_state != 0 or self.data.et.get.fault_str != NO_ERROR:
                    Pub().pub("openWB/set/optional/et/get/fault_state", 0)
                    Pub().pub("openWB/set/optional/et/get/fault_str", NO_ERROR)
        except Exception:
            log.exception("Fehler im Optional-Modul")

    def ocpp_transfer_meter_values(self):
        try:
            if self.data.ocpp.active:
                thread_handler(Thread(target=self._transfer_meter_values, args=(), name="OCPP Client"))
        except Exception:
            log.exception("Fehler im OCPP-Optional-Modul")

    def _transfer_meter_values(self):
        for cp in data.data.cp_data.values():
            try:
                if self.data.ocpp.boot_notification_sent is False:
                    # Boot-Notification nicht in der init-Funktion aufrufen, da noch nicht alles initialisiert ist
                    self.boot_notification(cp.data.config.ocpp_chargebox_id,
                                           cp.chargepoint_module.fault_state,
                                           cp.chargepoint_module.config.type,
                                           cp.data.get.serial_number)
                    self.data.ocpp.boot_notification_sent = True
                    Pub().pub("openWB/set/optional/ocpp/boot_notification_sent", True)
                if cp.data.set.ocpp_transaction_id is not None:
                    self.send_heart_beat(cp.data.config.ocpp_chargebox_id, cp.chargepoint_module.fault_state)
                    self.transfer_values(cp.data.config.ocpp_chargebox_id,
                                         cp.chargepoint_module.fault_state, cp.num, int(cp.data.get.imported))
            except Exception:
                log.exception("Fehler im OCPP-Optional-Modul")
