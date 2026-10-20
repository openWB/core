from dataclasses import dataclass


@dataclass
class BydConfiguration:
    username: str = ""
    password: str = ""
    # erforderlich, auch bei nur einem Fahrzeug am Account
    vin: str = ""
    # ISO-Ländercode, wie in der BYD-App unter "Land/Region" hinterlegt (z.B. "DE", "NL").
    # Bestimmt u.a. den Login-Endpunkt/die Sprache der API-Antworten.
    country_code: str = "DE"
    # "ev" (rein elektrisch) oder "hybrid" (PHEV). Bei Hybriden liefert die API
    # bei falscher Einstellung die EV-Reichweite/Verbrauchsfelder als 0 zurück.
    energy_type: str = "ev"
    # Login-Feld "identifierType", "0" = E-Mail (Standard). Bei manchen Accounts liefert
    # der Login trotz korrekter Zugangsdaten "Email or password is incorrect" zurück - laut
    # https://github.com/jkaberg/pyBYD/issues/71 evtl. abhängig vom Account-Typ ein anderer
    # Wert noetig, aber (Stand dort) noch nicht bestätigt. Vorsicht: jeder Loginversuch
    # zaehlt gegen das Fehlversuch-Limit des BYD-Accounts.
    identifier_type: str = "0"
    # Android-Geräte-Fingerprint (JSON), einmalig generiert und dauerhaft gespeichert, damit der
    # Account immer als dasselbe Gerät auftritt - siehe soc.py. Nicht vom Nutzer editierbar.
    device_fingerprint: str = ""


@dataclass
class Byd:
    name: str = "BYD"
    type: str = "byd"
    official: bool = False
    configuration: BydConfiguration = None

    def __post_init__(self):
        if self.configuration is None:
            self.configuration = BydConfiguration()
