from typing import Optional

from helpermodules.auto_str import auto_str


@auto_str
class PorscheConnectConfiguration:
    def __init__(self,
                 email: Optional[str] = None,        # My-Porsche E-Mail (Porsche ID), nur zur Anzeige
                 vin: Optional[str] = None,          # optional; leer -> erstes Fahrzeug im Konto
                 calculate_soc: bool = False,
                 # von der UI-Anmeldung ("Porsche verbinden") gefuellt. Das Passwort wird
                 # NICHT gespeichert - es dient nur transient dem Login und wird durch den
                 # refresh_token ersetzt.
                 access_token: str = "",
                 refresh_token: str = "",
                 expires_at: float = 0):
        self.email = email
        self.vin = vin
        self.calculate_soc = calculate_soc
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.expires_at = expires_at


@auto_str
class PorscheConnect:
    def __init__(self,
                 name: str = "Porsche Connect",
                 type: str = "porsche",
                 official: bool = False,
                 configuration: PorscheConnectConfiguration = None) -> None:
        self.name = name
        self.type = type
        # official=False: inoffizielle, reverse-engineerte Porsche-Connect-Schnittstelle
        self.official = official
        self.configuration = configuration or PorscheConnectConfiguration()
