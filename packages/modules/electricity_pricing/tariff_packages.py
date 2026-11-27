"""Die Anbieter für den Stromtarif liegen je nach Art des Preises in einem von drei Paketen. Der Typ des Anbieters ist
über alle Pakete eindeutig, gespeichert wird nur der Typ."""
from pathlib import Path
from typing import Tuple

from modules.electricity_pricing.price_type import PriceType

# Paket -> Art der Preise, die die Anbieter dieses Pakets liefern
TARIFF_PACKAGES = {
    "flexible_tariffs": PriceType.DYNAMIC,
    "timebased_tariffs": PriceType.TIME_DEPENDENT,
    "fixed_tariffs": PriceType.FIXED,
}


def find_tariff_package(tariff_type: str) -> str:
    for package in TARIFF_PACKAGES:
        if (Path(__file__).resolve().parent / package / tariff_type / "tariff.py").is_file():
            return package
    raise ValueError(f"Kein Stromtarif-Anbieter vom Typ '{tariff_type}' gefunden.")


def tariff_module_path(tariff_type: str) -> str:
    return f".electricity_pricing.{find_tariff_package(tariff_type)}.{tariff_type}.tariff"


def tariff_packages() -> Tuple[str, ...]:
    return tuple(TARIFF_PACKAGES)
