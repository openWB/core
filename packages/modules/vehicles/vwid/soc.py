import aiohttp
import logging
from asyncio import new_event_loop, set_event_loop
from typing import Union

from modules.common.abstract_device import DeviceDescriptor
from modules.common.abstract_vehicle import VehicleUpdateData
from modules.common.component_state import CarState
from modules.common.configurable_vehicle import ConfigurableVehicle
from modules.vehicles.vwid.config import VWId
from modules.vehicles.vwid import libvwid
from modules.vehicles.vwgroup.vwgroup import VwGroup

log = logging.getLogger(__name__)


def create_vehicle(vehicle_config: VWId, vehicle: int):
    def fetch() -> CarState:
        nonlocal vw_group

        # async method, called from sync fetch_soc, required because libvwid expect async environment
        async def _fetch_soc() -> Union[int, float, str]:
            async with aiohttp.ClientSession() as session:
                return await vw_group.request_data(libvwid.vwid(session))

        loop = new_event_loop()
        set_event_loop(loop)
        soc, range, soc_ts, soc_tsX = loop.run_until_complete(_fetch_soc())
        return CarState(soc=soc, range=range, soc_timestamp=soc_tsX)

    vw_group = VwGroup(vehicle_config, vehicle)

    def updater(vehicle_update_data: VehicleUpdateData) -> CarState:
        return fetch()
    return ConfigurableVehicle(vehicle_config=vehicle_config,
                               component_updater=updater,
                               vehicle=vehicle,
                               calc_while_charging=vehicle_config.configuration.calculate_soc)


device_descriptor = DeviceDescriptor(configuration_factory=VWId)
