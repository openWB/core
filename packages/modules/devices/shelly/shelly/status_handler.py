import logging
from typing import Dict
from typing import Tuple, List, Optional

from modules.common import req

log = logging.getLogger(__name__)

ALPHABETICAL_INDEX = ['a', 'b', 'c']


def get_generation(address: str) -> Tuple[Optional[int], str]:
    device_info = req.get_http_session().get(f"http://{address}/shelly", timeout=3).json()
    generation = 1  # default to gen 1
    if 'gen' in device_info:  # gen 2+
        generation = int(device_info['gen'])
    if 'model' in device_info:
        model = str(device_info['model'])
    elif 'type' in device_info:
        model = str(device_info['type'])
    log.debug(f"Device {model} at {address} is generation {generation}")
    return generation, model


def request_status(address: str, generation: Optional[int]) -> Dict:
    if generation == 1:
        status_url = "http://" + address + "/status"
    else:
        status_url = "http://" + address + "/rpc/Shelly.GetStatus"
    return req.get_http_session().get(status_url, timeout=3).json()


def parse_data(phase: int, factor: float, status: Dict) -> Tuple[
        List[float], Optional[List[float]], Optional[List[float]], Optional[List[float]], float, Optional[float]]:
    try:
        currents: Optional[List[float]] = None
        voltages: Optional[List[float]] = None
        power_factors: Optional[List[float]] = None
        frequency: Optional[float] = None

        # GEN 1
        if "meters" in status:
            currents = [0.0, 0.0, 0.0]
            powers = [0.0, 0.0, 0.0]
            voltages = [0.0, 0.0, 0.0]
            meters = status['meters']  # einphasiger shelly?
            for i in range(0, min(3, len(meters))):
                powers[(i+phase-1) % 3] = float(meters[i].get('power', 0)) * factor
                currents[(i+phase-1) % 3] = (float(meters[i].get('power', 0)) * factor) / 230
                voltages[(i+phase-1) % 3] = 230
            power = sum(powers)
        elif "emeters" in status:
            powers = [0.0, 0.0, 0.0]
            currents = [0.0, 0.0, 0.0]
            voltages = [0.0, 0.0, 0.0]
            power_factors = [0.0, 0.0, 0.0]
            meters = status['emeters']  # shellyEM & shelly3EM
            # shellyEM has one meter, shelly3EM has three meters
            for i in range(0, min(3, len(meters))):
                powers[(i+phase-1) % 3] = float(meters[i].get('power', 0)) * factor
                currents[(i+phase-1) % 3] = float(meters[i].get('current', 0)) * factor
                voltages[(i+phase-1) % 3] = float(meters[i].get('voltage', 0))
                power_factors[(i+phase-1) % 3] = float(meters[i].get('pf', 0))
            power = sum(powers)

        # GEN 2+
        # shelly Pro3EM
        elif "em:0" in status:
            powers = [0.0, 0.0, 0.0]
            currents = [0.0, 0.0, 0.0]
            voltages = [0.0, 0.0, 0.0]
            power_factors = [0.0, 0.0, 0.0]
            meters = status['em:0']
            for i, alphabetical_index in enumerate(ALPHABETICAL_INDEX):
                if meters.get(f'{alphabetical_index}_act_power') is None:
                    continue
                powers[(i+phase-1) % 3] = float(meters.get(f'{alphabetical_index}_act_power', 0)) * factor
                voltages[(i+phase-1) % 3] = float(meters.get(f'{alphabetical_index}_voltage', 0))
                currents[(i+phase-1) % 3] = float(meters.get(f'{alphabetical_index}_current', 0)) * factor
                power_factors[(i+phase-1) % 3] = float(meters.get(f'{alphabetical_index}_pf', 0))
            power = float(meters.get('total_act_power', 0)) * factor
        # Shelly MiniPM G3
        elif "pm1:0" in status:
            log.debug("single phase shelly")
            powers = [0.0, 0.0, 0.0]
            currents = [0.0, 0.0, 0.0]
            voltages = [0.0, 0.0, 0.0]
            power_factors = [0.0, 0.0, 0.0]
            meters = status['pm1:0']
            powers[phase-1] = meters['apower'] * factor
            voltages[phase-1] = meters['voltage']
            currents[phase-1] = meters['current'] * factor
            power_factors[phase-1] = meters.get('pf', 0)
            power = meters['apower'] * factor
            frequency = meters['freq']
        elif 'switch:0' in status and 'apower' in status['switch:0']:
            log.debug("single phase shelly")
            powers = [0.0, 0.0, 0.0]
            currents = [0.0, 0.0, 0.0]
            voltages = [0.0, 0.0, 0.0]
            power_factors = [0.0, 0.0, 0.0]
            meters = status['switch:0']
            powers[phase-1] = meters['apower'] * factor
            voltages[phase-1] = meters['voltage']
            currents[phase-1] = meters['current'] * factor
            if 'pf' in meters:
                power_factors[phase-1] = meters['pf']
            power = meters['apower'] * factor
            if 'freq' in meters:
                frequency = meters['freq']
        else:
            log.debug("single phase shelly")
            powers = [0.0, 0.0, 0.0]
            currents = [0.0, 0.0, 0.0]
            voltages = [0.0, 0.0, 0.0]
            power_factors = [0.0, 0.0, 0.0]
            meters = status['em1:0']
            powers[phase-1] = meters['act_power']
            voltages[phase-1] = meters['voltage']
            currents[phase-1] = meters['current'] * factor
            power_factors[phase-1] = meters['pf']
            power = meters['act_power'] * factor  # shelly Pro EM Gen 2
            frequency = meters['freq']

        return powers, voltages, currents, power_factors, power, frequency
    except KeyError:
        raise Exception("unsupported shelly device?")
