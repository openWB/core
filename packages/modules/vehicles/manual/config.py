class ManualSocConfiguration:
    def __init__(self) -> None:
        pass


class ManualSoc:
    def __init__(self,
                 name: str = "Manueller SoC",
                 type: str = "manual",
                 official: bool = True,
                 configuration: ManualSocConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.official = official
        self.configuration = configuration or ManualSocConfiguration()
