import logging
from typing import Dict, List, Optional, Tuple, Union
from helpermodules import timecheck

from helpermodules.auto_str import auto_str

log = logging.getLogger(__name__)


def _check_none(values: Optional[List[Optional[Union[int, float]]]]) -> bool:
    """Check if values is None or [None, None, None]
    Args:
        values: list of values
        Returns:
            True if values is None or [None, None, None]
    """
    return values is None or values == [None]*3


def _calculate_powers_and_currents(currents: Optional[List[Optional[float]]],
                                   powers: Optional[List[Optional[float]]],
                                   voltages: Optional[List[Optional[float]]]) -> Tuple[
        Optional[List[float]], List[float], List[float]]:
    """Calculate currents from powers and voltages or vice versa
    All args are optional, if one is None or [None, None, None] it will be calculated from the others if possible.
    Args:
        currents: list of currents for 3 phases in A
        powers: list of powers for 3 phases in W
        voltages: list of voltages for 3 phases in V
    Returns:
        currents, powers, voltages
    """
    if _check_none(voltages):
        voltages = [230.0]*3
    if _check_none(powers):
        if _check_none(currents):
            powers = [0.0]*3
        else:
            powers = [currents[i]*voltages[i] for i in range(0, 3)]
    if _check_none(currents) and not _check_none(powers):
        try:
            currents = [powers[i]/voltages[i] for i in range(0, 3)]
        except ZeroDivisionError:
            # some inverters (Sungrow) report 0V if in standby
            currents = [0.0]*3
    if not _check_none(currents) and not _check_none(powers):
        currents = [currents[i]*-1 if powers[i] < 0 and currents[i] > 0 else currents[i] for i in range(0, 3)]
    return currents, powers, voltages


def check_currents_power_sign(currents: Optional[List[Optional[float]]], power: float) -> bool:
    """Check if the sign of the sum of currents matches the power sign or both zero."""
    return any([
        sum(currents) < 0 and power < 0,
        sum(currents) > 0 and power > 0,
        sum(currents) == 0 and power == 0
    ])


@auto_str
class BatState:
    def __init__(
        self,
        imported: float = 0,
        exported: float = 0,
        power: float = 0,
        soc: float = 0,
        currents: Optional[List[float]] = None,
    ):
        """Args:
            imported: total imported energy in Wh
            exported: total exported energy in Wh
            power: actual power in W
            soc: actual state of charge in percent
        """
        self.imported = imported
        self.exported = exported
        self.power = power
        self.soc = soc
        if _check_none(currents):
            currents = [0.0]*3
        else:
            if not check_currents_power_sign(currents, power):
                log.debug("currents sign wrong "+str(currents))
        self.currents = currents


@auto_str
class CounterState:
    def __init__(
        self,
        imported: float = 0,
        exported: float = 0,
        power: float = 0,
        voltages: Optional[List[Optional[float]]] = None,
        currents: Optional[List[Optional[float]]] = None,
        powers: Optional[List[Optional[float]]] = None,
        power_factors: Optional[List[Optional[float]]] = None,
        frequency: float = 50,
        serial_number: str = "",
    ):
        """Args:
            imported: total imported energy in Wh
            exported: total exported energy in Wh
            power: actual power in W
            voltages: actual voltages for 3 phases in V
            currents: actual currents for 3 phases in A
            powers: actual powers for 3 phases in W
            power_factors: actual power factors for 3 phases
            frequency: actual grid frequency in Hz
        """
        self.currents, self.powers, self.voltages = _calculate_powers_and_currents(currents, powers, voltages)
        if _check_none(power_factors):
            power_factors = [0.0]*3
        self.power_factors = power_factors
        self.imported = imported
        self.exported = exported
        self.power = power
        self.frequency = frequency
        self.serial_number = serial_number


@auto_str
class InverterState:
    def __init__(
        self,
        exported: float,
        power: float,
        imported: float = 0,  # simulated import counter to properly calculate PV energy when bat is charged from AC
        currents: Optional[List[Optional[float]]] = None,
        dc_power: Optional[float] = None
    ):
        """Args:
            exported: total energy in Wh
            imported: total energy in Wh
            power: actual power in W
            currents: actual currents for 3 phases in A
            dc_power: dc power in W
        """
        if _check_none(currents):
            currents = [0.0]*3
        else:
            if not check_currents_power_sign(currents, power):
                log.debug("currents sign wrong "+str(currents))
        self.currents = currents
        self.power = power
        self.exported = exported
        self.imported = imported
        self.dc_power = dc_power


@auto_str
class CarState:
    def __init__(self, soc: float, range: Optional[float] = None, soc_timestamp: Optional[float] = None):
        """Args:
            soc: actual state of charge in percent
            range: actual range in km
            soc_timestamp: timestamp of last request as unix timestamp
        """
        self.soc = soc
        self.range = range
        if soc_timestamp is None:
            self.soc_timestamp = timecheck.create_timestamp()
        else:
            if soc_timestamp > 1e10:  # Convert soc_timestamp to seconds if it is in milliseconds
                log.debug(f'Zeitstempel {soc_timestamp} ist in ms, wird in s gewandelt. Modul sollte angepasst werden.')
                soc_timestamp /= 1000
            self.soc_timestamp = soc_timestamp


@auto_str
class ChargepointState:
    def __init__(self,
                 phases_in_use: int,
                 imported: float,
                 exported: float,
                 power: float,
                 currents: List[float],
                 charge_state: bool,
                 plug_state: bool,
                 serial_number: str = "",
                 charging_current: Optional[float] = 0,
                 charging_voltage: Optional[float] = 0,
                 charging_power: Optional[float] = 0,
                 evse_signaling: Optional[str] = None,
                 max_charge_power: Optional[float] = None,
                 max_discharge_power: Optional[float] = None,
                 powers: Optional[List[Optional[float]]] = None,
                 voltages: Optional[List[Optional[float]]] = None,
                 power_factors: Optional[List[Optional[float]]] = None,
                 rfid: Optional[str] = None,
                 rfid_timestamp: Optional[float] = None,
                 frequency: float = 50,
                 soc: Optional[float] = None,
                 soc_timestamp: Optional[int] = None,
                 evse_current: Optional[float] = None,
                 vehicle_id: Optional[str] = None,
                 max_evse_current: Optional[int] = None,
                 current_branch: Optional[str] = None,
                 current_commit: Optional[str] = None,
                 version: Optional[str] = None):
        self.currents, self.powers, self.voltages = _calculate_powers_and_currents(currents, powers, voltages)
        self.frequency = frequency
        self.imported = imported
        self.exported = exported
        self.power = power
        self.serial_number = serial_number
        self.phases_in_use = phases_in_use
        self.charge_state = charge_state
        self.plug_state = plug_state
        self.rfid = rfid
        self.rfid_timestamp = rfid_timestamp
        if _check_none(power_factors):
            power_factors = [0.0]*3
        self.charging_current = charging_current
        self.charging_power = charging_power
        self.charging_voltage = charging_voltage
        self.power_factors = power_factors
        self.soc = soc
        self.soc_timestamp = soc_timestamp
        self.evse_current = evse_current
        self.max_evse_current = max_evse_current
        self.vehicle_id = vehicle_id
        self.current_branch = current_branch
        self.current_commit = current_commit
        self.version = version
        self.evse_signaling = evse_signaling
        self.max_charge_power = max_charge_power
        self.max_discharge_power = max_discharge_power


@auto_str
class TariffState:
    def __init__(self,
                 prices: Optional[Dict[int, float]] = None) -> None:
        self.prices = prices


@auto_str
class IoState:
    """JSON erlaubt nur Zeichenketten als Schlüssel für Objekte"""

    def __init__(self, analog_input: Dict[str, float] = None,
                 digital_input: Dict[str, bool] = None,
                 analog_output: Dict[str, float] = None,
                 digital_output: Dict[str, bool] = None) -> None:
        self.analog_input = analog_input
        self.digital_input = digital_input
        self.analog_output = analog_output
        self.digital_output = digital_output


class EvseState:
    def __init__(self, plug_state: bool, charge_state: bool, set_current: int, max_current: int) -> None:
        self.plug_state = plug_state
        self.charge_state = charge_state
        self.set_current = set_current
        self.max_current = max_current
