#!/usr/bin/env python3
import logging

from modules.common.abstract_device import DeviceDescriptor
from modules.common.abstract_vehicle import VehicleUpdateData
from modules.common.component_state import CarState
from modules.common.configurable_vehicle import ConfigurableVehicle
from modules.vehicles.porsche.api import PorscheConnectApi
from modules.vehicles.porsche.config import PorscheConnect

log = logging.getLogger(__name__)


def create_vehicle(vehicle_config: PorscheConnect, vehicle: int):
    api = None

    def initializer():
        nonlocal api
        api = PorscheConnectApi(vehicle_config.configuration.email,
                                vehicle_config.configuration.password,
                                vehicle)

    def updater(vehicle_update_data: VehicleUpdateData) -> CarState:
        soc, range, soc_ts, odometer = api.fetch_soc(vehicle_config.configuration.vin)
        log.debug(f"Porsche SoC={soc}%, range={range}km, ts={soc_ts}, odo={odometer}km")
        return CarState(soc=soc, range=range, soc_timestamp=soc_ts, odometer=odometer)

    return ConfigurableVehicle(vehicle_config=vehicle_config,
                               component_updater=updater,
                               vehicle=vehicle,
                               initializer=initializer,
                               calc_while_charging=vehicle_config.configuration.calculate_soc)


device_descriptor = DeviceDescriptor(configuration_factory=PorscheConnect)
