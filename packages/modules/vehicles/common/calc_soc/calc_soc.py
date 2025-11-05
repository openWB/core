import logging

from modules.common.abstract_vehicle import VehicleUpdateData

log = logging.getLogger(__name__)


def calc_soc(vehicle_update_data: VehicleUpdateData,
             efficiency: int,
             last_imported: float,
             battery_capacity: float) -> float:
    imported_since_last_soc = vehicle_update_data.imported - last_imported
    energy_battery_gain = imported_since_last_soc * efficiency / 100
    battery_soc_gain = (energy_battery_gain / battery_capacity) * 100
    soc = vehicle_update_data.last_soc + battery_soc_gain
    log.debug(
        f"SoC-Gain: (({imported_since_last_soc/1000}kWh charged * {efficiency}% efficiency) / "
        f"{battery_capacity/1000}kWh battery-size) * 100 = {battery_soc_gain}%",
    )
    log.debug(f"{vehicle_update_data.last_soc}% + {energy_battery_gain / 1000}kWh = {soc}%")
    if soc > 100:
        log.warning(f"Calculated SoC of {soc}% exceeds maximum and is limited to 100%! Check your settings!")
        soc = 100
    return soc
