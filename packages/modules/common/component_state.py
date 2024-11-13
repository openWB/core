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


@auto_str
class BatState:
    def __init__(
        self,
        imported: float = 0,
        exported: float = 0,
        power: float = 0,
        soc: float = 0,
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


@auto_str
class InverterState:
    def __init__(
        self,
        exported: float,
        power: float,
        currents: Optional[List[Optional[float]]] = None,
        dc_power: Optional[float] = None
    ):
        """Args:
            exported: total energy in Wh
            power: actual power in W
            currents: actual currents for 3 phases in A
            dc_power: dc power in W
        """
        if _check_none(currents):
            currents = [0.0]*3
        else:
            if not ((sum(currents) < 0 and power < 0) or (sum(currents) > 0 and power > 0)):
                log.debug("currents sign wrong "+str(currents))
        self.currents = currents
        self.power = power
        self.exported = exported
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
            self.soc_timestamp = soc_timestamp


@auto_str
class ChargepointState:
    def __init__(self,
                 phases_in_use: int = 0,
                 imported: float = 0,
                 exported: float = 0,
                 power: float = 0,
                 serial_number: str = "",
                 charging_current: Optional[float] = 0,
                 charging_voltage: Optional[float] = 0,
                 charging_power: Optional[float] = 0,
                 powers: Optional[List[Optional[float]]] = None,
                 voltages: Optional[List[Optional[float]]] = None,
                 currents: Optional[List[Optional[float]]] = None,
                 power_factors: Optional[List[Optional[float]]] = None,
                 charge_state: bool = False,
                 plug_state: bool = False,
                 rfid: Optional[str] = None,
                 rfid_timestamp: Optional[float] = None,
                 frequency: float = 50,
                 soc: Optional[float] = None,
                 soc_timestamp: Optional[int] = None,
                 evse_current: Optional[float] = None,
                 vehicle_id: Optional[str] = None,
                 max_evse_current: Optional[int] = None):
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
        if self.rfid and rfid_timestamp is None:
            self.rfid_timestamp = timecheck.create_timestamp()
        else:
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


@auto_str
class TariffState:
    def __init__(self,
                 prices: Optional[Dict[int, float]] = None) -> None:
        self.prices = prices


@auto_str
class RcrState:
    def __init__(self, override_value: float) -> None:
        self.override_value = override_value
