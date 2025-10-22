#!/usr/bin/env python3
from modules.electricity_pricing.tariffs.fixed_hours.tariff import create_electricity_tariff as create_electricity_tariff_dynamic
from modules.electricity_pricing.tariffs.fixed_hours.config import FixedHoursTariff
from modules.common.abstract_device import DeviceDescriptor


def create_electricity_tariff(config: FixedHoursTariff):
    return create_electricity_tariff_dynamic(config)


device_descriptor = DeviceDescriptor(configuration_factory=FixedHoursTariff)
