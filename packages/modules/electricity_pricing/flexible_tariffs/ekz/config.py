class EkzTariffConfiguration:
    def __init__(self):
        self.country = "ch"
        self.unit = "Rp"
        self.update_hours = [18, 19]


class EkzTariff:
    def __init__(self,
                 name: str = "EKZ (CH)",
                 type: str = "ekz",
                 official: bool = False,
                 configuration: EkzTariffConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.official = official
        self.configuration = configuration or EkzTariffConfiguration()
