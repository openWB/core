class ManualSocConfiguration:
    def __init__(self) -> None:
        pass


class ManualSoc:
    def __init__(self,
                 name: str = "Manueller SoC",
                 type: str = "manual",
                 configuration: ManualSocConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.configuration = configuration or ManualSocConfiguration()
