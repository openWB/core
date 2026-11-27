#!/usr/bin/env python3
from modules.common.abstract_device import DeviceDescriptor
from modules.electricity_pricing.timebased_tariffs.fixed_hours.config import (FixedHoursTariff,
                                                                              FixedHoursTariffConfiguration)
from modules.electricity_pricing.timebased_tariffs.fixed_hours.tariff import (
    create_electricity_tariff as create_electricity_tariff_fixed_hours)
from modules.electricity_pricing.fixed_tariffs.fixed_price.config import FixedPriceTariff


def create_electricity_tariff(config: FixedPriceTariff):
    """Ein fester Preis ist eine Preisliste ohne Zeitfenster."""
    return create_electricity_tariff_fixed_hours(FixedHoursTariff(
        configuration=FixedHoursTariffConfiguration(default_price=config.configuration.default_price,
                                                    tariffs=[],
                                                    update_hours=config.configuration.update_hours)))


device_descriptor = DeviceDescriptor(configuration_factory=FixedPriceTariff)
