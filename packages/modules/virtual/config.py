class VirtualConfiguration:
    def __init__(self):
        pass


class Virtual:
    def __init__(self,
                 name: str = "Virtuelles Gerät",
                 type: str = "virtual",
                 id: int = 0,
                 configuration: VirtualConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.id = id
        self.configuration = configuration or VirtualConfiguration()


class VirtualCounterConfiguration:
    def __init__(self, external_consumption=400):
        self.external_consumption = external_consumption


class VirtualCounterSetup:
    def __init__(self,
                 name: str = "Virtueller Zähler",
                 type: str = "counter",
                 id: int = 0,
                 configuration: VirtualCounterConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.id = id
        self.configuration = configuration or VirtualCounterConfiguration()
