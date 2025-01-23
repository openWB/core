from typing import Optional, List, Dict


class FixedHoursTariffConfiguration:
    def __init__(self, default_price: Optional[float] = None, tariffs: List[Dict[str, any]] = []) -> None:
        self.default_price = default_price
        self.tariffs = tariffs
        '''
        Example configuration:
        "tariffs": [
            {
                "name": "high_tariff",
                "price": 0.20,
                "active_times": {
                    "quarters": [1, 2, 3, 4],  # applicable quarters
                    "times": [("08:00", "12:00"), ("18:00", "22:00")]  # active times during the day
                }
            },
            {
                "name": "low_tariff",
                "price": 0.05,
                "active_times": {
                    "quarters": [1, 2, 3, 4],  # applicable quarters
                    "times": [("00:00", "06:00"), ("22:00", "23:59")]  # active times during the day
                }
            }
        ]
        '''


class FixedHoursTariff:
    def __init__(self,
                 name: str = "Feste Tarifstunden (z.b. §14a EnWG Modul3)",
                 type: str = "fixed_hours",
                 configuration: FixedHoursTariffConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.configuration = configuration or FixedHoursTariffConfiguration()
