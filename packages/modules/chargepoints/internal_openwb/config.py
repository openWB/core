class InternalOpenWBConfiguration:
    def __init__(self):
        pass


class InternalOpenWB:
    def __init__(self,
                 name: str = "Interne openWB",
                 type: str = "internal_openwb",
                 id: int = 0,
                 configuration: InternalOpenWBConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.id = id
        self.configuration = configuration or InternalOpenWBConfiguration()
