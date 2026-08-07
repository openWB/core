from dataclasses import dataclass, field


@dataclass
class GroupeETariffConfiguration:
    country: str = "ch"
    unit: str = "Rp"


@dataclass
class GroupeETariff:
    name: str = "Groupe E (CH)"
    type: str = "groupe_e"
    official: bool = False
    configuration: GroupeETariffConfiguration = field(default_factory=GroupeETariffConfiguration)
