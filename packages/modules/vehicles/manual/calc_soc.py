import logging

from modules.common.abstract_soc import SocUpdateData

log = logging.getLogger(__name__)


def calc_soc(soc_update_data: SocUpdateData, efficiency: int, soc_start: float, battery_capacity: float) -> float:
    energy_battery_gain = soc_update_data.imported_since_plugged * efficiency
    battery_soc_gain = (energy_battery_gain / battery_capacity) * 100
    soc = soc_start + battery_soc_gain
    log.debug(
        "SoC-Gain: ((%g kWh Charged * %g%% efficiency) / %g kWh battery-size) * 100= %.1f%%",
        soc_update_data.imported_since_plugged/1000, battery_capacity/1000, efficiency, battery_soc_gain
    )
    log.debug("%g%% + %g kWh = %g%%", soc_start, energy_battery_gain / 1000, soc)
    if soc > 100:
        log.warning("Calculated SoC of %g%% exceeds maximum and is limited to 100%%! Check your settings!", soc)
        soc = 100
    return soc
