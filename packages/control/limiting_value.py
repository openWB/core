from dataclasses import dataclass
from enum import Enum
from typing import Optional


class LimitingValue(Enum):
    CURRENT = ", da der Maximal-Strom an Zähler {} erreicht ist."
    POWER = ", da die maximale Leistung an Zähler {} erreicht ist."
    UNBALANCED_LOAD = ", da die maximale Schieflast an Zähler {} erreicht ist."
    DIMMING = ", da die Dimmung die Ladeleistung begrenzt."
    DIMMING_VIA_DIRECT_CONTROL = ", da die Dimmung per Direkt-Steuerung die Ladeleistung auf 4,2 kW begrenzt."
    RIPPLE_CONTROL_RECEIVER = (", da der Ladepunkt durch den RSE-Kontakt auf {}% der konfigurierten Anschlussleistung "
                               "reduziert wird.")
    CONTROL_STEPWISE = "Leistung begrenzt auf {}%"
    CONTROLLABLE_CONSUMERS_ERROR = (", da aufgrund eines Fehlers im IO-Gerät {} die steuerbaren Verbraucher nur "
                                    "mit der minimalen Leistung betrieben werden können. Bitte prüfe die Status-Seite.")
    MISSING_CONFIGURATION = ", da die Konfiguration für die Aktion unvollständig ist."


@dataclass
class LoadmanagementLimit:
    message: Optional[str]
    limiting_value: Optional[LimitingValue]


def loadmanagement_limit_factory() -> LoadmanagementLimit:
    return LoadmanagementLimit(None, None)
