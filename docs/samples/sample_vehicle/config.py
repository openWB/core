class SampleVehicleSocConfiguration:
    def __init__(self) -> None:
        pass


class SampleVehicleSoc:
    def __init__(self,
                 name: str = "Sample Vehicle",
                 type: str = "sample_vehicle",
                 configuration: SampleVehicleSocConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.configuration = configuration or SampleVehicleSocConfiguration()
