"""Art des Preises eines Stromtarif-Anbieters.

Nur Anbieter mit zeitabhängigen oder dynamischen Preisen schalten das preisbasierte Laden frei. Ein fester Preis
wird für die Berechnung der Ladekosten, das Log und die Darstellung verwendet, es gibt aber keine günstigen oder
teuren Zeiten, nach denen geladen werden könnte.
"""
from enum import Enum


class PriceType(Enum):
    FIXED = "fixed"
    TIME_DEPENDENT = "time_dependent"
    DYNAMIC = "dynamic"


def get_price_type(config) -> PriceType:
    """Anbieter, die nichts angeben (alle Börsenpreis-Anbieter), sind dynamisch. Nur feste und zeitabhängige Anbieter
    legen am Config-Objekt ein ClassVar price_type fest."""
    return getattr(config, "price_type", PriceType.DYNAMIC)
