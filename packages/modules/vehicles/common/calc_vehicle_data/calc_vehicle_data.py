import logging

from modules.common.abstract_vehicle import VehicleUpdateData
from modules.common.component_state import CarState

log = logging.getLogger(__name__)


def calc_vehicle_data(vehicle_update_data: VehicleUpdateData,
                      last_imported: float) -> CarState:
    imported_since_last_soc = vehicle_update_data.imported - last_imported
    energy_battery_gain = imported_since_last_soc * vehicle_update_data.efficiency / 100
    battery_soc_gain = (energy_battery_gain / vehicle_update_data.battery_capacity) * 100
    _soc = vehicle_update_data.last_soc + battery_soc_gain
    _eff = vehicle_update_data.efficiency
    log.debug(
        f"SoC-Gain: (({imported_since_last_soc/1000}kWh charged * {_eff}% _eff) / "
        f"{vehicle_update_data.battery_capacity/1000}kWh battery-size) * 100 = {battery_soc_gain}%",
    )
    log.debug(f"{vehicle_update_data.last_soc}% + {energy_battery_gain / 1000}kWh = {_soc}%")
    if _soc > 100:
        log.warning(f"Calculated SoC of {_soc}% exceeds maximum and is limited to 100%! Check your settings!")
        _soc = 100
    _range = int(vehicle_update_data.battery_capacity * _soc / vehicle_update_data.average_consump)
    return CarState(soc=_soc, range=_range)
