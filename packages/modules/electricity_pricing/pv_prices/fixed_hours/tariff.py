#!/usr/bin/env python3
from modules.electricity_pricing.timebased_tariffs.fixed_hours.tariff \
    import create_electricity_tariff as create_electricity_tariff_fixed_hours
from modules.electricity_pricing.pv_prices.fixed_hours.config import FixedHoursPvPrice
from modules.common.abstract_device import DeviceDescriptor


def create_electricity_tariff(config: FixedHoursPvPrice):
    return create_electricity_tariff_fixed_hours(config)


device_descriptor = DeviceDescriptor(configuration_factory=FixedHoursPvPrice)
