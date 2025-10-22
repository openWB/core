class GroupeETariffConfiguration:
    def __init__(self):
        self.country = "ch"


class GroupeETariff:
    def __init__(self,
                 name: str = "Groupe E (CH)",
                 type: str = "groupe_e",
                 official: bool = False,
                 configuration: GroupeETariffConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.official = official
        self.configuration = configuration or GroupeETariffConfiguration()
