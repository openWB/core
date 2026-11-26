from dataclasses import dataclass, field


@dataclass
class GroupeETariffConfiguration:
    pass


@dataclass
class GroupeETariff:
    name: str = "Groupe E (CH)"
    type: str = "groupe_e"
    official: bool = False
    configuration: GroupeETariffConfiguration = field(default_factory=GroupeETariffConfiguration)
