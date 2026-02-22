from typing import List, Dict


class FixedHoursTariffConfiguration:
    def __init__(self,
                 default_price: float = 0,
                 tariffs: List[Dict[str, any]] = []) -> None:
        self.default_price = default_price
        self.tariffs = tariffs
        self.update_hours = list(range(24))
        '''
        Example configuration:
        "tariffs": [
            {
                "name": "high_tariff",
                "price": 0.20,
                "active_times": {
                    "dates": [("01-01", "31-03"), ("01-07", "30-09")],  # applicable date ranges (day-month)
                    "times": [("08:00", "12:00"), ("18:00", "22:00")]  # active times during the day
                }
            },
            {
                "name": "low_tariff",
                "price": 0.05,
                "active_times": {
                    "dates": [("01-04", "30-06"), ("01-10", "31-12")],  # applicable date ranges (day-month)
                    "times": [("00:00", "06:00"), ("22:00", "23:59")]  # active times during the day
                }
            }
        ]
        '''


class FixedHoursTariff:
    def __init__(self,
                 name: str = "Feste Tarifstunden (z.b. §14a EnWG Modul3)",
                 type: str = "fixed_hours",
                 official: bool = False,
                 configuration: FixedHoursTariffConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.official = official
        self.configuration = configuration or FixedHoursTariffConfiguration()
