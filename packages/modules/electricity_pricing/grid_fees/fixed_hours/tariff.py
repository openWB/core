#!/usr/bin/env python3
from modules.electricity_pricing.timebased_tariffs.fixed_hours.tariff \
    import create_electricity_tariff as create_electricity_tariff_dynamic
from modules.electricity_pricing.grid_fees.fixed_hours.config import FixedHoursGridFee
from modules.common.abstract_device import DeviceDescriptor


def create_electricity_tariff(config: FixedHoursGridFee):
    return create_electricity_tariff_dynamic(config)


device_descriptor = DeviceDescriptor(configuration_factory=FixedHoursGridFee)
