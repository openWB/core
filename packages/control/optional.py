"""Optionale Module
"""
import logging
from math import ceil
from threading import Thread
from typing import List

from control import data
from control.ocpp import OcppMixin
from control.optional_data import OptionalData
from helpermodules import hardware_configuration
from helpermodules.constants import NO_ERROR
from helpermodules.pub import Pub
from helpermodules import timecheck
from helpermodules.utils import thread_handler
from modules.common.configurable_tariff import ConfigurableElectricityTariff
from modules.common.configurable_monitoring import ConfigurableMonitoring

log = logging.getLogger(__name__)
AS_EURO_PER_KWH = 1000.0  # Umrechnung von €/Wh in €/kWh


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

    def et_charging_allowed(self, max_price: float) -> bool:
        """ prüft, ob der aktuelle Strompreis niedriger oder gleich der festgelegten Preisgrenze ist.

        Return
        ------
        True: Preis ist gleich oder liegt darunter
        False: Preis liegt darüber
        """
        try:
            if self.et_provider_available():
                current_price = self.et_get_current_price(prices=self.data.et.get.prices)
                log.info("Prüfe strompreisbasiertes Laden mit Preisgrenze %.5f €/kWh, aktueller Preis: %.5f €/kWh",
                         max_price * AS_EURO_PER_KWH,
                         current_price*AS_EURO_PER_KWH)
                return current_price <= max_price
            else:
                return True
        except KeyError:
            log.exception("Fehler beim strompreisbasierten Laden")
            self.et_get_prices()
        except Exception:
            log.exception("Fehler im Optional-Modul")
            return False

    def __get_first_entry(self, prices: dict[str, float]) -> tuple[str, float]:
        if self.et_provider_available():
            prices = self.data.et.get.prices
            timestamp, first = next(iter(prices.items()))
            price_timeslot_seconds = self.__calculate_price_timeslot_length(prices)
            now = int(timecheck.create_timestamp())
            prices = {
                price[0]: price[1]
                for price in prices.items()
                if int(price[0]) > now - (price_timeslot_seconds - 1)
            }
            self.data.et.get.prices = prices
            timestamp, first = next(iter(prices.items()))
            return timestamp, first
        else:
            raise Exception("Kein Anbieter für strompreisbasiertes Laden konfiguriert.")

    def __get_current_timeslot_start(self, prices: dict[str, float]) -> float:
        timestamp, first = self.__get_first_entry(prices)
        return timestamp

    def et_get_current_price(self, prices: dict[str, float]) -> float:
        timestamp, first = self.__get_first_entry(prices)
        return first

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
            first_timeslot_start = self.__get_current_timeslot_start(prices)
            price_candidates = {
                timestamp: price
                for timestamp, price in prices.items()
                if (
                    # is current timeslot or futur
                    int(timestamp) >= int(first_timeslot_start) and
                    # ends before plan target time
                    int(timestamp) + price_timeslot_seconds <= int(first_timeslot_start) + remaining_time
                    )
            }
            now = int(timecheck.create_timestamp())
            ordered_by_date_reverse = reversed(sorted(price_candidates.items(), key=lambda x: x[0]))
            ordered_by_price = sorted(ordered_by_date_reverse, key=lambda x: x[1])
            selected_time_slots = {int(i[0]): float(i[1])
                                   for i in ordered_by_price[:1 + ceil(duration/price_timeslot_seconds)]}
            selected_lenght = price_timeslot_seconds * (
                        len(selected_time_slots)-1) - (int(now) - min(selected_time_slots))
            return sorted(selected_time_slots.keys()
                          if not (min(selected_time_slots) > now or duration <= selected_lenght)
                          else [timestamp[0] for timestamp in iter(selected_time_slots.items())][:-1]
                          )
            # if sum() sorted([int(i[0]) for i in ordered_by_price][:ceil(duration/price_timeslot_seconds)])
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
