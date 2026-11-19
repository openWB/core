from pathlib import Path

import pytest

from modules.electricity_pricing.price_type import get_price_type
from modules.electricity_pricing.tariff_packages import TARIFF_PACKAGES, find_tariff_package, tariff_module_path

import importlib

PACKAGES_PATH = Path(__file__).resolve().parent


@pytest.mark.parametrize("tariff_type, package", [
    pytest.param("awattar", "flexible_tariffs", id="dynamic"),
    pytest.param("fixed_hours", "timebased_tariffs", id="time_based"),
    pytest.param("fixed_price", "fixed_tariffs", id="fixed"),
])
def test_find_tariff_package(tariff_type, package):
    assert find_tariff_package(tariff_type) == package
    assert tariff_module_path(tariff_type) == f".electricity_pricing.{package}.{tariff_type}.tariff"


def test_unknown_tariff_type_raises():
    with pytest.raises(ValueError):
        find_tariff_package("gibt_es_nicht")


def test_tariff_types_are_unique_over_all_packages():
    types = [path.parent.name for package in TARIFF_PACKAGES for path in (PACKAGES_PATH / package).glob("*/tariff.py")]
    assert len(types) == len(set(types))


@pytest.mark.parametrize("package, price_type", list(TARIFF_PACKAGES.items()))
def test_every_provider_has_the_price_type_of_its_package(package, price_type):
    for path in (PACKAGES_PATH / package).glob("*/tariff.py"):
        mod = importlib.import_module(f"modules.electricity_pricing.{package}.{path.parent.name}.tariff")
        config = mod.device_descriptor.configuration_factory()
        assert get_price_type(config) == price_type, path
