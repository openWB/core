from enum import Enum


class LimitingValue(Enum):
    CURRENT = ", da der Maximal-Strom an Zähler {} erreicht ist."
    POWER = ", da die maximale Leistung an Zähler {} erreicht ist."
    UNBALANCED_LOAD = ", da die maximale Schieflast an Zähler {} erreicht ist."
    DIMMING = ", da die Dimmung die Ladeleistung bgrenzt."
    DIMMING_VIA_DIRECT_CONTROL = ", da die Dimmung per Direkt-Steuerung die Ladeleistung begrenzt."
    RIPPLE_CONTROL_RECEIVER = (", da der Ladepunkt durch den RSE-Kontakt auf {}% der konfigurierten Anschlussleistung "
                               "reduziert wird.")
