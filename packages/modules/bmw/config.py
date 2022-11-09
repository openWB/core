class BMWConfiguration:
    def __init__(self, userid: str = "", password: str = "", vin: str = ""):
        self.userid = userid
        self.password = password
        self.vin = vin


class BMW:
    def __init__(self,
                 name: str = "BMW",
                 type: str = "bmw",
                 configuration: BMWConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.configuration = configuration or BMWConfiguration()
