from dataclasses import dataclass, field
from typing import Dict, Optional, Protocol

from dataclass_utils.factories import empty_dict_factory
from helpermodules.constants import NO_ERROR
from modules.display_themes.cards.config import CardsDisplayTheme


@dataclass
class PricingGet:
    fault_state: int = field(default=0)
    next_query_time: int = field(default=0)
    fault_str: str = field(default=NO_ERROR)
    prices: Dict = field(default_factory=empty_dict_factory)


def create_pricing_get_with_topics(topic_prefix: str) -> PricingGet:
    """Factory function to create PricingGet with custom topic prefix"""
    pricing_get = PricingGet()
    pricing_get.__dataclass_fields__['fault_state'].metadata = {"topic": f"{topic_prefix}/get/fault_state"}
    pricing_get.__dataclass_fields__['fault_str'].metadata = {"topic": f"{topic_prefix}/get/fault_str"}
    pricing_get.__dataclass_fields__['prices'].metadata = {"topic": f"{topic_prefix}/get/prices"}
    pricing_get.__dataclass_fields__['next_query_time'].metadata = {"topic": f"{topic_prefix}/get/next_query_time"}
    return pricing_get


def flexible_tariff_get_factory() -> PricingGet:
    return create_pricing_get_with_topics("ep/flexible_tariff")


def grid_fee_get_factory() -> PricingGet:
    return create_pricing_get_with_topics("ep/grid_fee")


@dataclass
class FlexibleTariff:
    get: PricingGet = field(default_factory=flexible_tariff_get_factory)
    name: str = field(default="flexible_tariff")


def get_flexible_tariff_factory() -> FlexibleTariff:
    return FlexibleTariff()


@dataclass
class GridFee:
    get: PricingGet = field(default_factory=grid_fee_get_factory)
    name: str = field(default="grid_fee")


def get_grid_fee_factory() -> GridFee:
    return GridFee()


@dataclass
class ElectricityPricingGet:
    _prices: Dict = field(default_factory=empty_dict_factory, metadata={"topic": "ep/prices"})

    @property
    def prices(self) -> Dict:
        return self._prices

    @prices.setter
    def prices(self, value: Dict):
        self._prices = value


def electricity_pricing_get_factory() -> ElectricityPricingGet:
    return ElectricityPricingGet()


@dataclass
class ElectricityPricing:
    configured: bool = field(default=False, metadata={"topic": "ep/configured"})
    flexible_tariff: FlexibleTariff = field(default_factory=get_flexible_tariff_factory)
    grid_fee: GridFee = field(default_factory=get_grid_fee_factory)
    get: ElectricityPricingGet = field(default_factory=electricity_pricing_get_factory)


def ep_factory() -> ElectricityPricing:
    return ElectricityPricing()


def cards_display_theme_factory() -> CardsDisplayTheme:
    return CardsDisplayTheme()


@dataclass
class InternalDisplay:
    active: bool = field(default=False, metadata={"topic": "int_display/active"})
    detected: bool = field(default=False, metadata={"topic": "int_display/detected"})
    on_if_plugged_in: bool = field(default=True, metadata={"topic": "int_display/on_if_plugged_in"})
    only_local_charge_points: bool = field(default=False, metadata={"topic": "int_display/only_local_charge_points"})
    pin_active: bool = field(default=False, metadata={"topic": "int_display/pin_active"})
    pin_code: str = field(default="0000", metadata={"topic": "int_display/pin_code"})
    rotation: int = field(default=0, metadata={"topic": "int_display/rotation"})
    standby: int = field(default=60, metadata={"topic": "int_display/standby"})
    theme: CardsDisplayTheme = field(default_factory=cards_display_theme_factory,
                                     metadata={"topic": "int_display/theme"})


def int_display_factory() -> InternalDisplay:
    return InternalDisplay()


@dataclass
class Rfid:
    active: bool = field(default=False, metadata={"topic": "rfid/active"})


def rfid_factory() -> Rfid:
    return Rfid()


@dataclass
class OcppConfig:
    active: bool = False
    url: Optional[str] = None
    version: str = "ocpp1.6"


def ocpp_config_factory() -> OcppConfig:
    return OcppConfig()


@dataclass
class Ocpp:
    config: OcppConfig = field(default_factory=ocpp_config_factory, metadata={"topic": "ocpp/config"})
    boot_notification_sent: bool = field(default=False, metadata={"topic": "ocpp/boot_notification_sent"})


def ocpp_factory() -> Ocpp:
    return Ocpp()


@dataclass
class OptionalData:
    electricity_pricing: ElectricityPricing = field(default_factory=ep_factory)
    int_display: InternalDisplay = field(default_factory=int_display_factory)
    rfid: Rfid = field(default_factory=rfid_factory)
    dc_charging: bool = field(default=False, metadata={"topic": "dc_charging"})
    ocpp: Ocpp = field(default_factory=ocpp_factory)


class OptionalProtocol(Protocol):
    @property
    def data(self) -> OptionalData: ...
