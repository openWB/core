"""Optionale Module
"""
from datetime import timedelta
import logging
from math import ceil
import random
from threading import Thread
from typing import List, Optional as TypingOptional
from datetime import datetime, timedelta

from control import data
from control.ocpp import OcppMixin
from control.optional_data import OptionalData
from helpermodules import hardware_configuration
from helpermodules.constants import NO_ERROR
from helpermodules.pub import Pub
from helpermodules import timecheck
from helpermodules.utils import thread_handler
from modules.common.configurable_tariff import ConfigurableFlexibleTariff, ConfigurableGridFee
from modules.common.configurable_monitoring import ConfigurableMonitoring

log = logging.getLogger(__name__)
AS_EURO_PER_KWH = 1000.0  # Umrechnung von €/Wh in €/kWh
TARIFF_UPDATE_HOUR = 14  # latest expected time for daily tariff update


class Optional(OcppMixin):
    def __init__(self):
        try:
            self.data = OptionalData()
            self.flexible_tariff_module: ConfigurableFlexibleTariff = None
            self.grid_fee_module: ConfigurableGridFee = None
            self.monitoring_module: ConfigurableMonitoring = None
            self.data.dc_charging = hardware_configuration.get_hardware_configuration_setting("dc_charging")
            Pub().pub("openWB/optional/dc_charging", self.data.dc_charging)
        except Exception:
            log.exception("Fehler im Optional-Modul")

    def monitoring_start(self):
        if self.monitoring_module is not None:
            self.monitoring_module.start_monitoring()

    def monitoring_stop(self):
        if self.monitoring_module is not None:
            self.monitoring_module.stop_monitoring()

    def ep_provider_available(self) -> bool:
        return self.flexible_tariff_module is not None or self.grid_fee_module is not None

    def ep_is_charging_allowed_hours_list(self, selected_hours: list[int]) -> bool:
        """ prüft, ob das strompreisbasiertes Laden aktiviert und ein günstiger Zeitpunkt ist.

        Parameter
        ---------
        selected_hours: list[int]
            Liste der ausgewählten günstigen Zeitslots (Unix-Timestamps)

        Return
        ------
        True: Der aktuelle Zeitpunkt liegt in einem ausgewählten günstigen Zeitslot
        False: Der aktuelle Zeitpunkt liegt in keinem günstigen Zeitslot
        """
        try:
            if self.ep_provider_available():
                return self.__get_current_timeslot_start(self.data.electricity_pricing.prices) in selected_hours
            else:
                log.info("Prüfe strompreisbasiertes Laden: Nicht konfiguriert")
                return False
        except Exception as e:
            log.exception(f"Fehler im Optional-Modul: {e}")
            return False

    def ep_is_charging_allowed_price_threshold(self, max_price: float) -> bool:
        """ prüft, ob der aktuelle Strompreis niedriger oder gleich der festgelegten Preisgrenze ist.

        Return
        ------
        True: Preis ist gleich oder liegt darunter
        False: Preis liegt darüber
        """
        try:
            if self.ep_provider_available():
                current_price = self.ep_get_current_price(prices=self.data.electricity_pricing.prices)
                log.info("Prüfe strompreisbasiertes Laden mit Preisgrenze %.5f €/kWh, aktueller Preis: %.5f €/kWh",
                         max_price * AS_EURO_PER_KWH,
                         current_price * AS_EURO_PER_KWH
                         )
                return current_price <= max_price
            else:
                return True
        except KeyError as e:
            log.exception("Fehler beim strompreisbasierten Laden: %s", e)
            return False
        except Exception as e:
            log.exception("Fehler im Optional-Modul: %s", e)
            return False

    def __get_first_entry(self, prices: dict[str, float]) -> tuple[str, float]:
        if self.ep_provider_available():
            prices = self.data.electricity_pricing.prices
            if prices is None or len(prices) == 0:
                raise Exception("Keine Preisdaten für strompreisbasiertes Laden vorhanden.")
            else:
                timestamp, first = next(iter(prices.items()))
                price_timeslot_seconds = self.__calculate_price_timeslot_length(prices)
                now = int(timecheck.create_timestamp())
                prices = {
                    price[0]: price[1]
                    for price in prices.items()
                    if int(price[0]) > now - (price_timeslot_seconds - 1)
                }
                self.data.electricity_pricing.prices = prices
                timestamp, first = next(iter(prices.items()))
                return timestamp, first
        else:
            raise Exception("Kein Anbieter für strompreisbasiertes Laden konfiguriert.")

    def __get_current_timeslot_start(self, prices: dict[str, float]) -> int:
        timestamp, first = self.__get_first_entry(prices)
        return int(timestamp)

    def ep_get_current_price(self, prices: dict[str, float]) -> float:
        timestamp, first = self.__get_first_entry(prices)
        return first

    def __calculate_price_timeslot_length(self, prices: dict) -> int:
        first_timestamps = list(prices.keys())[:2]
        return int(first_timestamps[1]) - int(first_timestamps[0])

    def ep_get_loading_hours(self, duration: float, remaining_time: float) -> List[int]:
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
        if self.ep_provider_available() is False:
            raise Exception("Kein Anbieter für strompreisbasiertes Laden konfiguriert.")
        try:
            prices = self.data.electricity_pricing.prices
            price_timeslot_seconds = self.__calculate_price_timeslot_length(prices)
            now = int(timecheck.create_timestamp())
            price_candidates = {
                timestamp: price
                for timestamp, price in prices.items()
                if (
                    # is current timeslot or futur
                    int(timestamp) + price_timeslot_seconds > now and
                    # ends before plan target time
                    not int(timestamp) >= now + remaining_time
                )
            }
            log.debug("%s Preis-Kandidaten in %s Sekunden zwischen %s Uhr und %s Uhr von %s Uhr bis %s Uhr",
                      len(price_candidates),
                      duration,
                      datetime.fromtimestamp(now),
                      datetime.fromtimestamp(now + remaining_time),
                      datetime.fromtimestamp(int(min(price_candidates))),
                      datetime.fromtimestamp(int(max(price_candidates))+price_timeslot_seconds))
            ordered_by_date_reverse = reversed(sorted(price_candidates.items(), key=lambda x: x[0]))
            ordered_by_price = sorted(ordered_by_date_reverse, key=lambda x: x[1])
            selected_time_slots = {int(i[0]): float(i[1])
                                   for i in ordered_by_price[:1 + ceil(duration/price_timeslot_seconds)]}
            selected_lenght = (
                price_timeslot_seconds * (len(selected_time_slots)-1) -
                (int(now) - min(selected_time_slots))
            )
            return sorted(selected_time_slots.keys()
                          if not (min(selected_time_slots) > now or duration <= selected_lenght)
                          else [timestamp[0] for timestamp in iter(selected_time_slots.items())][:-1]
                          )
            # if sum() sorted([int(i[0]) for i in ordered_by_price][:ceil(duration/price_timeslot_seconds)])
        except Exception as e:
            log.exception("Fehler im Optional-Modul: %s", e)
            return []

    def ep_get_prices(self):
        try:
            if self.et_price_update_required() is False:
                return
            if self.flexible_tariff_module:
                thread_handler(Thread(target=self.flexible_tariff_module.update, args=(), name="flexible tariff"))
            else:
                # Wenn kein Modul konfiguriert ist, Fehlerstatus zurücksetzen.
                if (self.data.electricity_pricing.flexible_tariff.get.fault_state != 0 or
                        self.data.electricity_pricing.flexible_tariff.get.fault_str != NO_ERROR):
                    self.data.electricity_pricing.flexible_tariff.get.fault_state = 0
                    self.data.electricity_pricing.flexible_tariff.get.fault_str = NO_ERROR
                    Pub().pub("openWB/set/optional/ep/flexible_tariff/get/fault_state", 0)
                    Pub().pub("openWB/set/optional/ep/flexible_tariff/get/fault_str", NO_ERROR)
            if self.grid_fee_module:
                thread_handler(Thread(target=self.grid_fee_module.update, args=(), name="grid fee"))
            else:
                # Wenn kein Modul konfiguriert ist, Fehlerstatus zurücksetzen.
                if (self.data.electricity_pricing.grid_fee.get.fault_state != 0 or
                        self.data.electricity_pricing.grid_fee.get.fault_str != NO_ERROR):
                    self.data.electricity_pricing.grid_fee.get.fault_state = 0
                    self.data.electricity_pricing.grid_fee.get.fault_str = NO_ERROR
                    Pub().pub("openWB/set/optional/ep/grid_fee/get/fault_state", 0)
                    Pub().pub("openWB/set/optional/ep/grid_fee/get/fault_str", NO_ERROR)
            self.data.electricity_pricing.prices = self.sum_prices()
            Pub().pub("openWB/set/optional/ep/prices", self.data.electricity_pricing.prices)
        except Exception as e:
            log.exception("Fehler im Optional-Modul: %s", e)

    def et_price_update_required(self) -> bool:
        def is_tomorrow(last_timestamp: str) -> bool:
            return (day_of(date=datetime.now()) < day_of(datetime.fromtimestamp(int(last_timestamp)))
                    or day_of(date=datetime.now()).hour < TARIFF_UPDATE_HOUR)

        def day_of(date: datetime) -> datetime:
            return date.replace(hour=0, minute=0, second=0, microsecond=0)

        def get_last_entry_time_stamp() -> str:
            last_known_timestamp = "0"
            if self.data.et.get.prices is not None:
                last_known_timestamp = max(self.data.et.get.prices)
            return last_known_timestamp
        if len(self.data.et.get.prices) == 0:
            return True
        if self.data.et.get.next_query_time is None:
            next_query_time = datetime.fromtimestamp(int(max(self.data.et.get.prices))).replace(
                hour=TARIFF_UPDATE_HOUR, minute=0, second=0
            ) + timedelta(
                # aktually ET providers issue next day prices up to half an hour earlier then 14:00
                # reduce serverload on their site by trying early and randomizing query time
                minutes=random.randint(1, 7) * -5
            )
            self.data.et.get.next_query_time = next_query_time.timestamp()
            Pub().pub("openWB/set/optional/et/get/next_query_time", self.data.et.get.next_query_time)
        if is_tomorrow(get_last_entry_time_stamp()):
            if timecheck.create_timestamp() > self.data.et.get.next_query_time:
                log.info(
                    f'Wartezeit {datetime.fromtimestamp(self.data.et.get.next_query_time).strftime("%Y%m%d-%H:%M:%S")}'
                    ' abgelaufen, Strompreise werden abgefragt')
                return True
            else:
                log.info(
                    'Nächster Abruf der Strompreise '
                    f'{datetime.fromtimestamp(self.data.et.get.next_query_time).strftime("%Y%m%d-%H:%M:%S")}.')
                return False
        return False

    def sum_prices(self):
        if self.flexible_tariff_module is None and self.grid_fee_module is not None:
            return self.data.electricity_pricing.grid_fee.get.prices
        if self.grid_fee_module is None and self.flexible_tariff_module is not None:
            return self.data.electricity_pricing.flexible_tariff.get.prices
        # Sortiere Keys
        grid_fee_prices = self.data.electricity_pricing.grid_fee.get.prices
        electricity_tariff_prices = self.data.electricity_pricing.flexible_tariff.get.prices
        grid_fee_keys = sorted(grid_fee_prices.keys())
        electricity_tariff_keys = sorted(electricity_tariff_prices.keys())
        # Typische Schrittweite bestimmen (Median der Deltas)

        def median_delta(keys):
            if len(keys) < 2:
                return timedelta.max
            deltas = [(keys[i+1] - keys[i]) for i in range(len(keys)-1)]
            deltas.sort()
            return timedelta(seconds=deltas[len(deltas)//2])
        grid_fee_delta = median_delta(grid_fee_keys)
        electricity_tariff_delta = median_delta(electricity_tariff_keys)
        # Feinere und gröbere Auflösung bestimmen
        if grid_fee_delta < electricity_tariff_delta:
            fine_dict, coarse_dict = grid_fee_prices, electricity_tariff_prices
        else:
            fine_dict, coarse_dict = electricity_tariff_prices, grid_fee_prices
        # Intervallgrenzen für das gröbere Dict
        coarse_keys = sorted(coarse_dict.keys())
        intervalle = []
        for i, start in enumerate(coarse_keys):
            if i+1 < len(coarse_keys):
                ende = coarse_keys[i+1]
            else:
                ende = max(fine_dict.keys()) + 1
            intervalle.append((start, ende))
        # Für jeden feinen Zeitstempel das passende grobe Intervall suchen und addieren
        result = {}
        for ts_fine, preis_fine in fine_dict.items():
            coarse_value = None
            for start, ende in intervalle:
                if start <= ts_fine < ende:
                    coarse_value = coarse_dict[start]
                    break
            if coarse_value is None:
                raise ValueError(f"Kein passendes Intervall für {ts_fine}")
            result[ts_fine] = preis_fine + coarse_value
        return result

    def ocpp_transfer_meter_values(self):
        try:
            if self.data.ocpp.active:
                thread_handler(Thread(target=self._transfer_meter_values, args=(), name="OCPP Client"))
        except Exception as e:
            log.exception("Fehler im OCPP-Optional-Modul: %s", e)

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
