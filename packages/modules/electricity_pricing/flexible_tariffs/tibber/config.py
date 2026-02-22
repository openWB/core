from typing import Optional


class TibberTariffConfiguration:
    def __init__(self, token: Optional[str] = None, home_id: Optional[str] = None):
        self.token = token
        self.home_id = home_id
        self.update_hours = [14]  # tibber publishes once daily before 14:00
        '''
         dynamische Netzentgelte müssen umgerechnet werden,
         damit der Gesamtpreis nicht um den Normalpreis der Netzentgelte verzerrt wird.
        '''
        self.includes_grid_fee = True


class TibberTariff:
    def __init__(self,
                 name: str = "Tibber",
                 type: str = "tibber",
                 official: bool = True,
                 configuration: TibberTariffConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.official = official
        self.configuration = configuration or TibberTariffConfiguration()
