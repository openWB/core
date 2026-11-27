from modules.electricity_pricing.bat_prices.fixed_hours.tariff import device_descriptor as bat_descriptor
from modules.electricity_pricing.feed_in_prices.fixed_hours.tariff import device_descriptor as feed_in_descriptor
from modules.electricity_pricing.pv_prices.fixed_hours.tariff import device_descriptor as pv_descriptor


def test_source_price_descriptors_are_fixed_hours_with_own_names():
    pv = pv_descriptor.configuration_factory()
    bat = bat_descriptor.configuration_factory()
    feed_in = feed_in_descriptor.configuration_factory()

    assert (pv.type, pv.name) == ("fixed_hours", "Fester Preis für Erzeugung")
    assert (bat.type, bat.name) == ("fixed_hours", "Fester Preis für Speicherentladung")
    assert (feed_in.type, feed_in.name) == ("fixed_hours", "Feste Einspeisevergütung")
