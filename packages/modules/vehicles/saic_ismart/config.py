from dataclasses import dataclass
from typing import Optional


@dataclass
class SaicIsmartConfiguration:
    username: str = ""
    password: str = ""
    # True, wenn der Benutzername eine E-Mail-Adresse ist (Standard). Manche Accounts
    # sind stattdessen per Telefonnummer registriert - dann hier auf False stellen und
    # phone_country_code setzen.
    username_is_email: bool = True
    phone_country_code: Optional[str] = None
    # erforderlich, auch bei nur einem Fahrzeug am Account
    vin: str = ""
    # Cloud-Region, wie in der MG-iSMART-App hinterlegt: eu (Standard), au, tr
    region: str = "eu"


@dataclass
class SaicIsmart:
    name: str = "MG iSMART (SAIC)"
    type: str = "saic_ismart"
    official: bool = False
    configuration: SaicIsmartConfiguration = None

    def __post_init__(self):
        if self.configuration is None:
            self.configuration = SaicIsmartConfiguration()
