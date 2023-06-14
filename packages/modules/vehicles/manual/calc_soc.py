import logging

from modules.common.abstract_soc import SocUpdateData

log = logging.getLogger(__name__)


def calc_soc(soc_update_data: SocUpdateData, efficiency: int, soc_start: float, battery_capacity: float) -> float:
    energy_battery_gain = soc_update_data.imported_since_plugged * efficiency
    battery_soc_gain = (energy_battery_gain / battery_capacity) * 100
    soc = soc_start + battery_soc_gain
    log.debug(
        f"SoC-Gain: (({soc_update_data.imported_since_plugged/1000}kWh charged * {efficiency}% efficiency) / "
        f"{battery_capacity/1000}kWh battery-size) * 100 = {battery_soc_gain}%",
    )
    log.debug(f"{soc_start}% + {energy_battery_gain / 1000}kWh = {soc}%")
    if soc > 100:
        log.warning(f"Calculated SoC of {soc}% exceeds maximum and is limited to 100%! Check your settings!")
        soc = 100
    return soc
