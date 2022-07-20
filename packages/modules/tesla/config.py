from typing import Optional


class TeslaConfiguration:
    def __init__(self, password: Optional[str] = None, email: Optional[str] = None, ip_address: Optional[str] = None):
        self.password = password
        self.email = email
        self.ip_address = ip_address


class Tesla:
    def __init__(self,
                 name: str = "Tesla",
                 type: str = "tesla",
                 id: int = 0,
                 configuration: TeslaConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.id = id
        self.configuration = configuration or TeslaConfiguration()


class TeslaBatConfiguration:
    def __init__(self):
        pass


class TeslaBatSetup:
    def __init__(self,
                 name: str = "Tesla Speicher",
                 type: str = "bat",
                 id: int = 0,
                 configuration: TeslaBatConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.id = id
        self.configuration = configuration or TeslaBatConfiguration()


class TeslaCounterConfiguration:
    def __init__(self):
        pass


class TeslaCounterSetup:
    def __init__(self,
                 name: str = "Tesla Zähler",
                 type: str = "counter",
                 id: int = 0,
                 configuration: TeslaCounterConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.id = id
        self.configuration = configuration or TeslaCounterConfiguration()


class TeslaInverterConfiguration:
    def __init__(self):
        pass


class TeslaInverterSetup:
    def __init__(self,
                 name: str = "Tesla Wechselrichter",
                 type: str = "inverter",
                 id: int = 0,
                 configuration: TeslaInverterConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.id = id
        self.configuration = configuration or TeslaInverterConfiguration()


class TeslaSocToken:
    def __init__(self,
                 refresh_token: str = "",
                 access_token: str = "",
                 expires_in: int = 0,
                 created_at: int = 0) -> None:
        self.refresh_token = refresh_token
        self.access_token = access_token
        self.expires_in = expires_in
        self.created_at = created_at


class TeslaSocConfiguration:
    def __init__(self, tesla_ev_num: int = 0, token: TeslaSocToken = None) -> None:
        self.tesla_ev_num = tesla_ev_num
        self.token = token or TeslaSocToken()


class TeslaSoc:
    def __init__(self,
                 name: str = "Tesla",
                 type: str = "tesla",
                 configuration: TeslaSocConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.configuration = configuration or TeslaSocConfiguration()
