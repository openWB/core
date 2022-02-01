from typing import List


class BatState:
    def __init__(self, imported: float = 0, exported: float = 0, power: float = 0, soc: float = 0):
        self.imported = imported
        self.exported = exported
        self.power = power
        self.soc = soc


class CounterState:
    def __init__(self,
                 imported: float = 0,
                 exported: float = 0,
                 power: float = 0,
                 voltages: List[float] = None,
                 currents: List[float] = None,
                 powers: List[float] = None,
                 power_factors: List[float] = None,
                 frequency: float = 50):
        if voltages is None:
            voltages = [0.0]*3
        self.voltages = voltages
        self.currents = currents
        if powers is None:
            powers = [0.0]*3
        self.powers = powers
        if power_factors is None:
            power_factors = [0.0]*3
        self.power_factors = power_factors
        self.imported = imported
        self.exported = exported
        self.power = power
        self.frequency = frequency


class InverterState:
    def __init__(
        self,
        counter: float,
        power: float,
        currents: List[float] = None,
    ):
        if currents is None:
            currents = [0.0]*3
        self.currents = currents
        self.power = power
        self.counter = counter


class CarState:
    def __init__(self, soc: float):
        self.soc = soc


class ChargepointState:
    def __init__(self,
                 imported: float = 0,
                 exported: float = 0,
                 power: float = 0,
                 voltages: List[float] = None,
                 currents: List[float] = None,
                 power_factors: List[float] = None,
                 phases_in_use: int = 1,
                 charge_state: bool = False,
                 plug_state: bool = False):
        if voltages is None:
            voltages = [0.0]*3
        self.voltages = voltages
        if currents is None:
            currents = [0.0]*3
        self.currents = currents
        if power_factors is None:
            power_factors = [0.0]*3
        self.power_factors = power_factors
        self.imported = imported
        self.exported = exported
        self.power = power
        self.phases_in_use = phases_in_use
        self.charge_state = charge_state
        self.plug_state = plug_state
