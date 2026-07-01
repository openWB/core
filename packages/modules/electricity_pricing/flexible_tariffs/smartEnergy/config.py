from dataclasses import dataclass, field


@dataclass
class SmartEnergyTariffConfiguration:
    pass


@dataclass
class SmartEnergyTariff:
    name: str = "smartEnergy"
    type: str = "smartEnergy"
    official: bool = True
    configuration: SmartEnergyTariffConfiguration = field(default_factory=SmartEnergyTariffConfiguration)
