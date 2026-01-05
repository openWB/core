from dataclasses import dataclass, field
from datetime import datetime, timedelta
import random
from typing import Dict, Optional, Protocol

from dataclass_utils.factories import empty_dict_factory
from helpermodules.constants import NO_ERROR
from helpermodules.pub import Pub
from modules.display_themes.cards.config import CardsDisplayTheme

TARIFF_UPDATE_HOUR = 14  # latest expected time for daily tariff update


@dataclass
class PricingGet:
    fault_state: int = 0
    fault_str: str = NO_ERROR
    prices: Dict = field(default_factory=empty_dict_factory)


def get_factory() -> PricingGet:
    return PricingGet()


@dataclass
class FlexibleTariff:
    get: PricingGet = field(default_factory=get_factory)


def get_flexible_tariff_factory() -> FlexibleTariff:
    return FlexibleTariff()


@dataclass
class GridFee:
    get: PricingGet = field(default_factory=get_factory)


def get_grid_fee_factory() -> GridFee:
    return GridFee()


@dataclass
class ElectricityPricingGet:
    next_query_time: Optional[float] = None
    _prices: Dict = field(default_factory=empty_dict_factory)

    @property
    def prices(self) -> Dict:
        return self._prices

    @prices.setter
    def prices(self, value: Dict):
        self._prices = value
        if value:
            next_query_time = datetime.fromtimestamp(float(max(value))).replace(
                hour=TARIFF_UPDATE_HOUR, minute=0, second=0
            ) + timedelta(
                # actully ET providers issue next day prices up to half an hour earlier then 14:00
                # reduce serverload on their site by trying early and randomizing query time
                minutes=random.randint(1, 7) * -5
            )
            Pub().pub("openWB/set/optional/ep/get/next_query_time", next_query_time.timestamp())


def electricity_pricing_get_factory() -> ElectricityPricingGet:
    return ElectricityPricingGet()


@dataclass
class ElectricityPricing:
    configured: bool = False
    flexible_tariff: FlexibleTariff = field(default_factory=get_flexible_tariff_factory)
    grid_fee: GridFee = field(default_factory=get_grid_fee_factory)
    get: ElectricityPricingGet = field(default_factory=electricity_pricing_get_factory)


def ep_factory() -> ElectricityPricing:
    return ElectricityPricing()


@dataclass
class InternalDisplay:
    active: bool = False
    on_if_plugged_in: bool = True
    pin_active: bool = False
    pin_code: str = "0000"
    standby: int = 60
    theme: CardsDisplayTheme = CardsDisplayTheme()


def int_display_factory() -> InternalDisplay:
    return InternalDisplay()


@dataclass
class Led:
    active: bool = False


def led_factory() -> Led:
    return Led()


@dataclass
class Rfid:
    active: bool = False


def rfid_factory() -> Rfid:
    return Rfid()


@dataclass
class Ocpp:
    active: bool = False
    boot_notification_sent: bool = False
    _url: Optional[str] = None
    version: str = "ocpp1.6"
    dummy_id_tag: Optional[str] = None

    @property
    def url(self) -> Optional[str]:
        return self._url

    @url.setter
    def url(self, value: Optional[str]):
        if value is not None and not value.endswith("/"):
            self._url = value + "/"
        else:
            self._url = value


def ocpp_factory() -> Ocpp:
    return Ocpp()


@dataclass
class OptionalData:
    electricity_pricing: ElectricityPricing = field(default_factory=ep_factory)
    int_display: InternalDisplay = field(default_factory=int_display_factory)
    led: Led = field(default_factory=led_factory)
    rfid: Rfid = field(default_factory=rfid_factory)
    dc_charging: bool = False
    ocpp: Ocpp = field(default_factory=ocpp_factory)


class OptionalProtocol(Protocol):
    @property
    def data(self) -> OptionalData: ...
