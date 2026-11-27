from dataclasses import dataclass

from modules.electricity_pricing.timebased_tariffs.fixed_hours.config import FixedHoursTariff


@dataclass
class FixedHoursGridFee(FixedHoursTariff):
    name: str = "Feste Netzentgelte (z.B. §14a EnWG Modul 3)"
