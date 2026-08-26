from typing import Optional

from helpermodules.auto_str import auto_str


@auto_str
class PorscheConnectConfiguration:
    def __init__(self,
                 email: Optional[str] = None,        # My-Porsche E-Mail (Porsche ID)
                 password: Optional[str] = None,     # My-Porsche Passwort
                 vin: Optional[str] = None,          # optional; leer -> erstes Fahrzeug im Konto
                 calculate_soc: bool = False):
        self.email = email
        self.password = password
        self.vin = vin
        self.calculate_soc = calculate_soc


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
