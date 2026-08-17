# import aiohttp
import logging
# from asyncio import new_event_loop, set_event_loop
# from typing import Union

from modules.common.abstract_device import DeviceDescriptor
from modules.common.abstract_vehicle import VehicleUpdateData
from modules.common.component_state import CarState
from modules.common.configurable_vehicle import ConfigurableVehicle
from modules.vehicles.vweuda.config import VWEUDA
from modules.vehicles.vweuda import libeuda
# from modules.vehicles.vwgroup.vwgroup import VwGroup

log = logging.getLogger(__name__)


def fetch(vehicle_update_data: VehicleUpdateData, config: VWEUDA, vehicle: int) -> CarState:
    soc, range, soc_ts, soc_tsX, odometer = libeuda.fetch_soc(config, vehicle, vehicle_update_data)
    log.debug(f"soc return: soc={soc}, range={range}, soc_ts={soc_ts}, soc_tsX={soc_tsX}, odometer={odometer}")
    return CarState(soc=soc, range=range, soc_timestamp=soc_ts, odometer=odometer)


def create_vehicle(vehicle_config: VWEUDA, vehicle: int):
    def updater(vehicle_update_data: VehicleUpdateData) -> CarState:
        return fetch(vehicle_update_data, vehicle_config, vehicle)

    return ConfigurableVehicle(vehicle_config=vehicle_config,
                               component_updater=updater,
                               vehicle=vehicle,
                               calc_while_charging=vehicle_config.configuration.calculate_soc)


device_descriptor = DeviceDescriptor(configuration_factory=VWEUDA)
