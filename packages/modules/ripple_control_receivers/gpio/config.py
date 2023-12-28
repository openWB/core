class GpioRcrConfiguration:
    def __init__(self):
        pass


class GpioRcr:
    def __init__(self,
                 name: str = "GPIOs auf der AddOn-Platine",
                 type: str = "gpio",
                 configuration: GpioRcrConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.configuration = configuration or GpioRcrConfiguration()
