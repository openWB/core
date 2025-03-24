from typing import Optional


class OctopusEnergyTariffConfiguration:
    def __init__(self,
                 email: Optional[str] = None,
                 accountId: Optional[str] = None,
                 password: Optional[str] = None):
        self.email = email
        self.accountId = accountId
        self.password = password


class OctopusEnergyTariff:
    def __init__(self,
                 name: str = "Octopus Energy Deutschland",
                 type: str = "octopusenergy",
                 configuration: OctopusEnergyTariffConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.configuration = configuration or OctopusEnergyTariffConfiguration()
