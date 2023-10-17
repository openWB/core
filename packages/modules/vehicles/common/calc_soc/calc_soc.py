import logging

from modules.common.abstract_vehicle import VehicleUpdateData

log = logging.getLogger(__name__)


def calc_soc(vehicle_update_data: VehicleUpdateData,
             efficiency: int,
             imported_start: float,
             soc_start: float,
             battery_capacity: float) -> float:
    imported_since_start = vehicle_update_data.imported - imported_start
    energy_battery_gain = imported_since_start * efficiency / 100
    battery_soc_gain = (energy_battery_gain / battery_capacity) * 100
    soc = soc_start + battery_soc_gain
    log.debug(
        f"SoC-Gain: (({imported_since_start/1000}kWh charged * {efficiency}% efficiency) / "
        f"{battery_capacity/1000}kWh battery-size) * 100 = {battery_soc_gain}%",
    )
    log.debug(f"{soc_start}% + {energy_battery_gain / 1000}kWh = {soc}%")
    if soc > 100:
        log.warning(f"Calculated SoC of {soc}% exceeds maximum and is limited to 100%! Check your settings!")
        soc = 100
    return soc
