class VWIdConfiguration:
    def __init__(self, userid: str = "", password: str = "", vin: str = ""):
        self.userid = userid
        self.password = password
        self.vin = vin


class VWId:
    def __init__(self,
                 name: str = "VWId",
                 type: str = "vwid",
                 configuration: VWIdConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.configuration = configuration or VWIdConfiguration()
