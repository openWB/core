#!/usr/bin/env python3
import logging
import time

from modules.common.abstract_device import DeviceDescriptor
from modules.common.abstract_vehicle import VehicleUpdateData
from modules.common.component_state import CarState
from modules.common.configurable_vehicle import ConfigurableVehicle
from modules.vehicles.tesla import api
from modules.vehicles.tesla.config import TeslaSoc

log = logging.getLogger(__name__)


def fetch(vehicle_config: TeslaSoc, vehicle_update_data: VehicleUpdateData) -> CarState:
    vehicle_config.configuration.token = api.validate_token(vehicle_config.configuration.token)
    if vehicle_update_data.charge_state is False:
        try:
            _wake_up_car(vehicle_config)
        except Exception as e:
            log.warning(
                f"Fehler beim Aufwecken des Fahrzeugs: {e}\n"
                "Der abgerufene SoC-Wert ist möglicherweise veraltet."
            )
    soc, range, soc_timestamp, odometer = api.request_data(
        vehicle=vehicle_config.configuration.tesla_ev_num, token=vehicle_config.configuration.token)
    return CarState(soc=soc, range=range, soc_timestamp=soc_timestamp, odometer=odometer)


def _wake_up_car(vehicle_config: TeslaSoc):
    log.debug("Waking up car.")
    counter = 0
    state = "offline"
    while counter <= 12:
        state = api.post_wake_up_command(
            vehicle=vehicle_config.configuration.tesla_ev_num, token=vehicle_config.configuration.token)
        if state == "online":
            break
        counter = counter+1
        time.sleep(5)
        log.debug(f"Loop: {counter}, State: {state}")
    log.info(f"Status nach Aufwecken: {state}")
    if state != "online":
        raise Exception(f"EV konnte nicht geweckt werden. Status: {state}")


def create_vehicle(vehicle_config: TeslaSoc, vehicle: int):
    def updater(vehicle_update_data: VehicleUpdateData) -> CarState:
        return fetch(vehicle_config, vehicle_update_data)
    return ConfigurableVehicle(vehicle_config=vehicle_config,
                               component_updater=updater,
                               vehicle=vehicle)


device_descriptor = DeviceDescriptor(configuration_factory=TeslaSoc)
