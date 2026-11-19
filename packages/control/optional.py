"""Optionale Module
"""
from dataclasses import asdict
import logging
from math import ceil
from threading import Thread
from typing import Dict, List, Optional as TypingOptional, Union
from datetime import datetime

from control import data
from control.ocpp import OcppMixin
from control.optional_data import (BatPrice, FeedInPrice, FlexibleTariff, ForecastGet, GridFee, OptionalData,
                                   PricingGet, PvPrice)
from helpermodules import hardware_configuration
from helpermodules.constants import NO_ERROR
from helpermodules.pub import Pub
from helpermodules import timecheck
from helpermodules.utils import thread_handler
from modules.common.configurable_forecast import ConfigurableForecast
from modules.common.configurable_tariff import ConfigurableFlexibleTariff, ConfigurableGridFee
from modules.common.configurable_monitoring import ConfigurableMonitoring
from modules.electricity_pricing.price_type import PriceType, get_price_type

log = logging.getLogger(__name__)
AS_EURO_PER_KWH = 1000.0  # Umrechnung von €/Wh in €/kWh
MQTT_PREFIX = "openWB/set/optional/ep"
# Rückfallwerte in €/Wh, solange kein Preisanbieter bzw. keine Preisliste vorliegt
FALLBACK_PRICES = {"grid": 0.0003, "pv": 0.00015, "bat": 0.0002, "feed_in": 0.00008}
# Preiskanäle, die nicht in den kombinierten Strompreis (ep/get/prices) einfließen
SOURCE_PRICES = ("pv_price", "bat_price", "feed_in_price")


def _source_price_module_property(source: str) -> property:
    attribute = f"_{source}_module"

    def getter(self):
        return getattr(self, attribute)

    def setter(self, value):
        if (value is None or
                (getattr(self, attribute) and value and getattr(self, attribute).config != value.config)):
            module_data = getattr(self.data.electricity_pricing, source)
            module_data.get = PricingGet()
            self._reset_source_price_state(module_data)
        setattr(self, attribute, value)

    return property(getter, setter)


class Optional(OcppMixin):
    def __init__(self):
        try:
            self.data = OptionalData()
            self._flexible_tariff_module: TypingOptional[ConfigurableFlexibleTariff] = None
            self._grid_fee_module: TypingOptional[ConfigurableGridFee] = None
            for source in SOURCE_PRICES:
                setattr(self, f"_{source}_module", None)
            self._forecast_module: TypingOptional[ConfigurableForecast] = None
            self.monitoring_module: TypingOptional[ConfigurableMonitoring] = None
            self.data.dc_charging = hardware_configuration.get_hardware_configuration_setting("dc_charging")
            Pub().pub("openWB/optional/dc_charging", self.data.dc_charging)
        except Exception:
            log.exception("Fehler im Optional-Modul")

    @property
    def flexible_tariff_module(self) -> TypingOptional[ConfigurableFlexibleTariff]:
        return self._flexible_tariff_module

    @flexible_tariff_module.setter
    def flexible_tariff_module(self, value: TypingOptional[ConfigurableFlexibleTariff]):
        if (value is None or
                (self._flexible_tariff_module and value and
                 self._flexible_tariff_module.config != value.config)):
            self.data.electricity_pricing.flexible_tariff.get = PricingGet()
            self._reset_state(self.data.electricity_pricing.flexible_tariff)
        self._flexible_tariff_module = value
        self._set_ep_configured()

    @property
    def grid_fee_module(self) -> TypingOptional[ConfigurableGridFee]:
        return self._grid_fee_module

    @property
    def forecast_module(self) -> TypingOptional[ConfigurableForecast]:
        return self._forecast_module

    @forecast_module.setter
    def forecast_module(self, value: TypingOptional[ConfigurableForecast]):
        if (value is None or
                (self._forecast_module and value and
                 self._forecast_module.config != value.config)):
            self.data.forecast.get = ForecastGet()
            self._reset_forecast_state()
        previous_configured = self.data.forecast.configured
        self._forecast_module = value
        if value is None:
            self.data.forecast.configured = False
            self.data.forecast.provider = None
            if previous_configured is not False:
                Pub().pub("openWB/set/optional/forecast/configured", False)
        else:
            self.data.forecast.configured = True
            self.data.forecast.provider = asdict(value.config)
            if previous_configured is not True:
                Pub().pub("openWB/set/optional/forecast/configured", True)

    def _reset_forecast_state(self):
        Pub().pub("openWB/set/optional/forecast/get/fault_state", 0)
        Pub().pub("openWB/set/optional/forecast/get/fault_str", NO_ERROR)
        Pub().pub("openWB/set/optional/forecast/get/force_update", False)
        Pub().pub("openWB/set/optional/forecast/get/values", {})
        Pub().pub("openWB/set/optional/forecast/get/today_values", {})
        Pub().pub("openWB/set/optional/forecast/get/tomorrow_values", {})
        Pub().pub("openWB/set/optional/forecast/get/daily_kwh", {})
        Pub().pub("openWB/set/optional/forecast/get/today_kwh", 0.0)
        Pub().pub("openWB/set/optional/forecast/get/tomorrow_kwh", 0.0)
        Pub().pub("openWB/set/optional/forecast/get/next_query_time", 0)
        Pub().pub("openWB/set/optional/forecast/get/last_update_time", 0)

    @grid_fee_module.setter
    def grid_fee_module(self, value: TypingOptional[ConfigurableGridFee]):
        if (value is None or
                (self._grid_fee_module and value and
                 self._grid_fee_module.config != value.config)):
            self.data.electricity_pricing.grid_fee.get = PricingGet()
            self._reset_state(self.data.electricity_pricing.grid_fee)
        self._grid_fee_module = value
        self._set_ep_configured()

    pv_price_module = _source_price_module_property("pv_price")
    bat_price_module = _source_price_module_property("bat_price")
    feed_in_price_module = _source_price_module_property("feed_in_price")

    def _reset_source_price_state(self, module: Union[PvPrice, BatPrice, FeedInPrice]):
        Pub().pub(f"{MQTT_PREFIX}/{module.name}/get/fault_state", 0)
        Pub().pub(f"{MQTT_PREFIX}/{module.name}/get/fault_str", NO_ERROR)
        Pub().pub(f"{MQTT_PREFIX}/{module.name}/get/prices", {})
        Pub().pub(f"{MQTT_PREFIX}/{module.name}/get/next_query_time", None)
        Pub().pub(f"{MQTT_PREFIX}/{module.name}/get/last_update_time", 0)
        Pub().pub(f"{MQTT_PREFIX}/{module.name}/get/force_update", False)

    def _has_price_provider(self) -> bool:
        """Es gibt einen Stromtarif oder Netzentgelte, deren Preise abgerufen, geloggt und angezeigt werden."""
        return self._flexible_tariff_module is not None or self._grid_fee_module is not None

    def _set_ep_configured(self):
        """configured: Es gibt einen Stromtarif oder Netzentgelte, die Preise werden angezeigt und geloggt.
        controllable: Preisbasiertes Laden ist möglich. Das ist nur bei zeitabhängigen oder dynamischen Preisen
        sinnvoll, ein fester Stromtarif liefert nur den Preis für die Ladekosten."""
        has_price_based_tariff = (self._flexible_tariff_module is not None and
                                  get_price_type(self._flexible_tariff_module.config) != PriceType.FIXED)
        configured = self._has_price_provider()
        controllable = self._grid_fee_module is not None or has_price_based_tariff
        self.data.electricity_pricing.configured = configured
        self.data.electricity_pricing.controllable = controllable
        Pub().pub("openWB/set/optional/ep/configured", configured)
        Pub().pub("openWB/set/optional/ep/controllable", controllable)

    def _reset_state(self, module: Union[FlexibleTariff, GridFee]):
        if (module.get.fault_state != 0 or module.get.fault_str != NO_ERROR):
            module.get.fault_state = 0
            module.get.fault_str = NO_ERROR
            Pub().pub(f"openWB/set/optional/ep/{module.name}/get/fault_state", 0)
            Pub().pub(f"openWB/set/optional/ep/{module.name}/get/fault_str", NO_ERROR)
        Pub().pub(f"openWB/set/optional/ep/{module.name}/get/prices", {})
        Pub().pub(f"openWB/set/optional/ep/{module.name}/get/next_query_time", None)
        Pub().pub(f"openWB/set/optional/ep/{module.name}/get/last_update_time", 0)
        Pub().pub(f"openWB/set/optional/ep/{module.name}/get/force_update", False)
        Pub().pub("openWB/set/optional/ep/get/prices", {})

    def monitoring_start(self):
        if self.monitoring_module is not None:
            self.monitoring_module.start_monitoring()

    def monitoring_stop(self):
        if self.monitoring_module is not None:
            self.monitoring_module.stop_monitoring()

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
            if self.data.electricity_pricing.controllable:
                return self.__get_current_timeslot_start() in selected_hours
            else:
                log.debug("Prüfe strompreisbasiertes Laden: Nicht konfiguriert")
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
            if self.data.electricity_pricing.controllable:
                current_price = self.ep_get_current_price()
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

    def __get_first_entry(self) -> tuple[str, float]:
        prices = self.data.electricity_pricing.get.prices
        if prices is None or len(prices) == 0:
            raise Exception("Keine Preisdaten für strompreisbasiertes Laden vorhanden.")
        else:
            timestamp, first = next(iter(prices.items()))
            return timestamp, first

    def remove_outdated_prices(self):
        def remove(price_data: Dict, last_active_timestamp: int = 0) -> Dict:
            now = timecheck.create_timestamp()
            first_timestamp = (max([timestamp for timestamp in price_data.keys()
                                    if float(timestamp) <= now], default=0))
            return {int(timestamp): price for timestamp, price in price_data.items()
                    if int(timestamp) >= int(first_timestamp) and
                    (int(timestamp) <= last_active_timestamp if last_active_timestamp > 0 else True)}

        try:
            ep = self.data.electricity_pricing
            if self._has_price_provider():
                #  prices lists are updated in optional_data via mqtt listener
                if len(ep.get.prices) > 0:
                    Pub().pub(f"{MQTT_PREFIX}/get/prices", remove(ep.get.prices))
                if self._flexible_tariff_module:
                    Pub().pub(f"{MQTT_PREFIX}/flexible_tariff/get/prices", remove(ep.flexible_tariff.get.prices))
                if self._grid_fee_module:
                    Pub().pub(f"{MQTT_PREFIX}/grid_fee/get/prices",
                              remove(ep.grid_fee.get.prices,
                                     last_active_timestamp=int(max(ep.get.prices.keys()))
                                     if ep.get.prices else 0))
            for source in SOURCE_PRICES:
                if getattr(self, f"_{source}_module"):
                    source_data = getattr(ep, source)
                    Pub().pub(f"{MQTT_PREFIX}/{source}/get/prices", remove(source_data.get.prices))
        except Exception as e:
            log.exception("Fehler beim Entfernen veralteter Preise: %s", e)

    def __get_current_timeslot_start(self) -> int:
        timestamp = self.__get_first_entry()[0]
        return int(timestamp)

    def ep_get_current_price(self) -> float:
        if self._has_price_provider():
            first = self.__get_first_entry()[1]
            return first
        else:
            raise Exception("Kein Anbieter für strompreisbasiertes Laden konfiguriert.")

    def get_current_price(self, source: str) -> float:
        """Aktueller Preis in €/Wh für "grid", "pv", "bat" oder "feed_in" (Einspeisung).
        Liegt kein Preis vor, wird der Rückfallwert aus FALLBACK_PRICES verwendet."""
        try:
            if source == "grid":
                return self.ep_get_current_price()
            prices = getattr(self.data.electricity_pricing, f"{source}_price").get.prices
            now = timecheck.create_timestamp()
            current = max((float(timestamp) for timestamp in prices if float(timestamp) <= now), default=None)
            if current is None:
                raise Exception(f"Keine Preisdaten für {source} vorhanden.")
            return next(price for timestamp, price in prices.items() if float(timestamp) == current)
        except Exception:
            return FALLBACK_PRICES[source]

    def forecast_get_current_value(self) -> TypingOptional[float]:
        """Liefert den aktuellen Prognosewert. Anders als bei den Strompreisen enthält
        today_values auch bereits vergangene Stunden des Tages, es wird also hier (statt schon
        beim Speichern) nach dem letzten Zeitstempel <= jetzt gefiltert."""
        today_values = self.data.forecast.get.today_values
        if not today_values:
            return None
        now = timecheck.create_timestamp()
        past_or_current = [timestamp for timestamp in today_values if float(timestamp) <= now]
        if not past_or_current:
            return None
        closest_timestamp = max(past_or_current, key=float)
        return today_values[closest_timestamp]

    def __calculate_price_timeslot_length(self, prices: dict) -> int:
        first_timestamps = sorted(list(prices.keys()))[:2]
        return float(first_timestamps[1]) - float(first_timestamps[0])

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
        if self.data.electricity_pricing.controllable is False:
            raise Exception("Kein Anbieter für strompreisbasiertes Laden konfiguriert.")
        try:
            prices = self.data.electricity_pricing.get.prices
            log.debug("Berechne günstige Zeit-Slots für strompreisbasiertes Laden, "
                      "benötigte Ladezeit: %.2f Sekunden, Restzeit bis Termin: %.2f Sekunden",
                      duration, remaining_time)
            log.debug("Verfügbare Preise: %s", prices)
            price_timeslot_seconds = self.__calculate_price_timeslot_length(prices)
            log.debug("Preis-Zeitslot-Länge: %.2f Sekunden", price_timeslot_seconds)
            now = timecheck.create_timestamp()
            price_candidates = {
                timestamp: price
                for timestamp, price in prices.items()
                if (
                    # is current timeslot or futur
                    float(timestamp) + price_timeslot_seconds > now and
                    # ends before plan target time
                    not float(timestamp) >= now + remaining_time
                )
            }
            log.debug("%s Preis-Kandidaten in %s Sekunden zwischen %s Uhr und %s Uhr von %s Uhr bis %s Uhr",
                      len(price_candidates),
                      duration,
                      datetime.fromtimestamp(now),
                      datetime.fromtimestamp(now + remaining_time),
                      datetime.fromtimestamp(float(min(price_candidates, default=0))),
                      datetime.fromtimestamp(float(max(price_candidates, default=0))+price_timeslot_seconds))
            ordered_by_date_reverse = reversed(sorted(price_candidates.items(), key=lambda x: x[0]))
            ordered_by_price = sorted(ordered_by_date_reverse, key=lambda x: x[1])
            selected_time_slots = {float(i[0]): float(i[1])
                                   for i in ordered_by_price[:1 + ceil(duration/price_timeslot_seconds)]}
            selected_lenght = (
                price_timeslot_seconds * (len(selected_time_slots)-1) -
                (float(now) - min(selected_time_slots, default=now))
            )
            return sorted(selected_time_slots.keys()
                          if not (min(selected_time_slots, default=0) > now or duration <= selected_lenght)
                          else [timestamp[0] for timestamp in iter(selected_time_slots.items())][:-1]
                          )
            # if sum() sorted([int(i[0]) for i in ordered_by_price][:ceil(duration/price_timeslot_seconds)])
        except Exception as e:
            log.exception("Fehler im Optional-Modul: %s", e)
            return []

    def _is_et_price_update_required_for_module(
            self, module: Union[FlexibleTariff, GridFee, PvPrice, BatPrice, FeedInPrice]) -> bool:
        if module.get.force_update or module.get.next_query_time is None:
            return True
        now = timecheck.create_timestamp()
        next_query_formatted = datetime.fromtimestamp(module.get.next_query_time).strftime("%Y%m%d-%H:%M:%S")
        if now > module.get.next_query_time:
            log.debug(f'Wartezeit {next_query_formatted} für {module.name} abgelaufen, Strompreise werden abgefragt')
            return True
        else:
            log.debug(f'Nächster Abruf der {module.name} Strompreise {next_query_formatted}.')
            return False

    def et_price_update_required(self) -> bool:
        self._set_ep_configured()
        ep = self.data.electricity_pricing
        if any(getattr(self, f"_{source}_module") is not None and
               self._is_et_price_update_required_for_module(getattr(ep, source)) for source in SOURCE_PRICES):
            return True
        if not self._has_price_provider():
            return False
        if len(self.data.electricity_pricing.get.prices) == 0:
            return True
        return ((self._flexible_tariff_module is not None and
                self._is_et_price_update_required_for_module(self.data.electricity_pricing.flexible_tariff)) or
                (self._grid_fee_module is not None and
                self._is_et_price_update_required_for_module(self.data.electricity_pricing.grid_fee)))

    def ocpp_transfer_meter_values(self):
        try:
            if self.data.ocpp.config.active:
                thread_handler(Thread(target=self._transfer_meter_values, args=(), name="OCPP Client"))
        except Exception as e:
            log.exception("Fehler im OCPP-Optional-Modul: %s", e)

    def _transfer_meter_values(self):
        for cp in data.data.cp_data.values():
            try:
                if self.data.ocpp.boot_notification_sent is False:
                    self.data.ocpp.boot_notification_sent = True
                    # Boot-Notification nicht in der init-Funktion aufrufen, da noch nicht alles initialisiert ist
                    self.boot_notification(cp.data.config.ocpp_chargebox_id,
                                           cp.chargepoint_module.fault_state,
                                           cp.chargepoint_module.config.type,
                                           cp.data.get.serial_number)
                if cp.data.set.ocpp_transaction_id is not None:
                    self.send_heart_beat(cp.data.config.ocpp_chargebox_id, cp.chargepoint_module.fault_state)
                    self.transfer_values(cp.data.config.ocpp_chargebox_id,
                                         cp.chargepoint_module.fault_state,
                                         cp.num,
                                         cp.data.set.ocpp_transaction_id,
                                         int(cp.data.get.imported))
            except Exception:
                log.exception("Fehler im OCPP-Optional-Modul")
