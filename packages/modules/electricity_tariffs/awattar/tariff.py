#!/usr/bin/env python3
from dataclasses import dataclass
from typing import Dict

from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_state import TariffState
from modules.common import req
from modules.electricity_tariffs.awattar.config import AwattarTariffConfiguration
from modules.electricity_tariffs.awattar.config import AwattarTariff


@dataclass
class CountryData:
    # awattar_fee: float
    # sales_tax: float  # Umsatzsteuer
    url: str

# Die Daten werden um 14.00 für den Folgetag veröffentlicht.


# Berechnung Brutto-Arbeitspreis für Österreich nicht möglich, da wesentlich komplexer.
    # Antwort aWATTar:
    # In Österreich werden Netzentgelte/Abgaben ganz anderes behandelt und sind im Unterschied zu Deutschland
    # auch nicht Teil des Vertrages mit aWATTar. In Österreich haben wir keine Möglichkeit, die Netzentgelte
    # vorab eindeutig zu bestimmen und führen dies normalerweise auch nicht auf. Es ist in Österreich auch möglich,
    # dass die Netzentgelte nicht an uns, sondern direkt an den Netzbetreiber entrichtet werden.
    # In anderen Worten, leider kann man das Verfahren aus Deutschland in Österreich nicht anwenden.
# Basispreis war in 1.9 fest auf 0 in main.sh. D.h. es wurde weder Basispreis noch die Umsatzsteuer berücksichtigt.
at = CountryData(url='https://api.awattar.at/v1/marketdata')
de = CountryData(url='https://api.awattar.de/v1/marketdata')


def fetch_prices(config: AwattarTariffConfiguration) -> Dict[int, float]:
    country_data: CountryData = globals()[config.country]
    raw_prices = req.get_http_session().get(
        country_data.url, headers={'Content-Type': 'application/json'}, timeout=(2, 6)).json()['data']
    prices: Dict[int, float] = {}
    for data in raw_prices:
        formatted_price = data["marketprice"]/1000000  # €/MWh -> €/Wh
        timestamp = data["start_timestamp"]/1000  # Epoch from ms in s
        prices.update({str(int(timestamp)): formatted_price})
    return prices


def create_electricity_tariff(config: AwattarTariff):
    def updater():
        return TariffState(prices=fetch_prices(config.configuration))
    return updater


device_descriptor = DeviceDescriptor(configuration_factory=AwattarTariff)
