#!/usr/bin/env python3
import logging
import datetime
import time
from typing import List, Tuple, Dict

from modules.electricity_tariffs.fixed_hours.config import FixedHoursTariff, FixedHoursTariffConfiguration
from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_state import TariffState
# from modules.common.configurable_tariff import ConfigurableTariff

log = logging.getLogger(__name__)


def to_time(time_str: str) -> datetime.time:
    if time_str == "24:00":
        return datetime.time(23, 59, 59)
    return datetime.datetime.strptime(time_str, "%H:%M").time()


def to_date(date_str: str, time_slot: datetime.datetime) -> datetime.date:
    date = datetime.datetime.strptime(date_str, "%d-%m").date().replace(year=datetime.datetime.now().year)
    if date.year < time_slot.year:  # Beim Jahreswechsel das korrekte Jahr setzen
        date = date.replace(year=time_slot.year)
    return date


def validate_tariff_times(config: FixedHoursTariffConfiguration) -> None:
    time_slots: List[Tuple[datetime.time, datetime.time, List[Tuple[str, str]]]] = []
    for tariff in config.tariffs:
        for start, end in tariff["active_times"]["times"]:
            start_time = to_time(start)
            end_time = to_time(end)
            for existing_start, existing_end, existing_dates in time_slots:
                if (start_time < existing_end and end_time > existing_start and
                        any(start <= existing_end and end >= existing_start for start, end in existing_dates)):
                    raise ValueError(f"Overlapping time window detected: {start} - {end} in tariff '{tariff['name']}'")
            time_slots.append((start_time, end_time, tariff["active_times"]["dates"]))


def fetch(config: FixedHoursTariffConfiguration) -> TariffState:
    validate_tariff_times(config)

    current_time = datetime.datetime.now().replace(minute=0, second=0, microsecond=0)
    prices: Dict[str, float] = {}

    for i in range(24):  # get prices for the next 24 hours
        time_slot = current_time + datetime.timedelta(hours=i)
        epoch_time = int(time.mktime(time_slot.timetuple()))
        price = config.default_price / 1000

        for tariff in config.tariffs:
            active_times = [(to_time(start), to_time(end)) for start, end in tariff["active_times"]["times"]]
            active_dates = [
                (to_date(start, time_slot), to_date(end, time_slot))
                for start, end in tariff["active_times"]["dates"]
            ]
            if (any(start <= time_slot.time() < end for start, end in active_times) and
                    any(start <= time_slot.date() <= end for start, end in active_dates)):
                price = tariff["price"] / 1000
                break  # Break since we found a matching tariff

        prices[str(epoch_time)] = price

    return TariffState(prices=prices)


def create_electricity_tariff(config: FixedHoursTariff):
    def updater() -> TariffState:
        return fetch(config.configuration)
    return updater


device_descriptor = DeviceDescriptor(configuration_factory=FixedHoursTariff)
