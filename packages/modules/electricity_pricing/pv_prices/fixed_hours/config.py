from dataclasses import dataclass

from modules.electricity_pricing.timebased_tariffs.fixed_hours.config import FixedHoursTariff


@dataclass
class FixedHoursPvPrice(FixedHoursTariff):
    name: str = "Fester Preis für Erzeugung"
