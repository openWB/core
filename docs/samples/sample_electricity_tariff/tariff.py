#!/usr/bin/env python3
import logging

from docs.samples.sample_electricity_tariff.config import SampleTariff, SampleTariffConfiguration
from modules.common import req
from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_state import TariffState
from modules.common.configurable_tariff import ConfigurableTariff

log = logging.getLogger(__name__)


def fetch(config: SampleTariffConfiguration) -> None:
    # request prices
    response = req.get_http_session().get().json()
    return TariffState(prices=response["price_list"])


def create_electricity_tariff(config: SampleTariff):
    def updater():
        return fetch(config.configuration)
    return updater


device_descriptor = DeviceDescriptor(configuration_factory=SampleTariff)
