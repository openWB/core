from dataclasses import dataclass, field
from typing import ClassVar

from modules.electricity_pricing.price_type import PriceType


@dataclass
class FixedPriceTariffConfiguration:
    default_price: float = 0.0003  # €/Wh
    update_hours: list[int] = field(default_factory=lambda: list(range(24)))


@dataclass
class FixedPriceTariff:
    name: str = "Fester Preis"
    type: str = "fixed_price"
    official: bool = True
    configuration: FixedPriceTariffConfiguration = field(default_factory=FixedPriceTariffConfiguration)
    # Ein fester Preis schaltet das preisbasierte Laden nicht frei
    price_type: ClassVar[PriceType] = PriceType.FIXED
