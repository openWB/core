from dataclasses import dataclass


@dataclass
class CurrentValues:
    bat_power: float = 0
    bat_soc: float = 0
    cp_power: float = 0
    evu_power: float = 0
    home_consumption: float = 0
    pv_power: float = 0
