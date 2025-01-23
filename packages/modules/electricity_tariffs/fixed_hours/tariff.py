#!/usr/bin/env python3
import logging
import datetime
import time

from modules.electricity_tariffs.fixed_hours.config import FixedHoursTariff, FixedHoursTariffConfiguration
from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_state import TariffState
# from modules.common.configurable_tariff import ConfigurableTariff

log = logging.getLogger(__name__)


def to_time(time_str):
    if time_str == "24:00":
        return datetime.time(23, 59, 59)
    return datetime.datetime.strptime(time_str, "%H:%M").time()


def validate_tariff_times(config):
    time_slots = []
    for tariff in config.tariffs:
        for start, end in tariff["active_times"]["times"]:
            start_time = to_time(start)
            end_time = to_time(end)
            for existing_start, existing_end in time_slots:
                if (start_time < existing_end and end_time > existing_start):
                    raise ValueError(f"Overlapping time window detected: {start} - {end} in tariff '{tariff['name']}'")
            time_slots.append((start_time, end_time))


def fetch(config: FixedHoursTariffConfiguration) -> None:
    validate_tariff_times(config)

    current_time = datetime.datetime.now().replace(minute=0, second=0, microsecond=0)
    prices = {}

    for i in range(24):  # get prices for the next 24 hours
        time_slot = current_time + datetime.timedelta(hours=i)
        epoch_time = int(time.mktime(time_slot.timetuple()))
        quarter = (current_time.month - 1) // 3 + 1
        price = config.default_price/1000

        for tariff in config.tariffs:
            active_times = [(to_time(start), to_time(end)) for start, end in tariff["active_times"]["times"]]
            if (any(start <= time_slot.time() < end for start, end in active_times) and
                    quarter in tariff["active_times"]["quarters"]):
                price = tariff["price"]/1000
                break  # Break since we found a matching tariff

        prices[str(epoch_time)] = price

    return TariffState(prices=prices)


def create_electricity_tariff(config: FixedHoursTariff):
    def updater():
        return fetch(config.configuration)
    return updater


device_descriptor = DeviceDescriptor(configuration_factory=FixedHoursTariff)
