class ManualSocConfiguration:
    def __init__(self, efficiency: float = 0.9, soc_start: float = 0) -> None:
        self.efficiency = efficiency
        self.soc_start = soc_start  # don't show in UI


class ManualSoc:
    def __init__(self,
                 name: str = "Manueller SoC",
                 type: str = "manual",
                 configuration: ManualSocConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.configuration = configuration or ManualSocConfiguration()
