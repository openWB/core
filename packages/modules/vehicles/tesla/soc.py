#!/usr/bin/env python3
import json
import logging
import time
from typing import List

from dataclass_utils import asdict, dataclass_from_dict
from helpermodules.cli import run_using_positional_cli_args
from modules.common.abstract_device import DeviceDescriptor
from modules.common.abstract_vehicle import VehicleUpdateData
from modules.common.component_state import CarState
from modules.common.configurable_vehicle import ConfigurableVehicle
from modules.vehicles.tesla import api
from modules.vehicles.tesla.config import TeslaSoc, TeslaSocConfiguration, TeslaSocToken

log = logging.getLogger(__name__)


def fetch(vehicle_config: TeslaSoc, vehicle_update_data: VehicleUpdateData) -> CarState:
    vehicle_config.configuration.token = api.validate_token(vehicle_config.configuration.token)
    if vehicle_update_data.charge_state is False:
        _wake_up_car(vehicle_config)
    soc, range, soc_timestamp = api.request_soc_range(
        vehicle=vehicle_config.configuration.tesla_ev_num, token=vehicle_config.configuration.token)
    return CarState(soc=soc, range=range, soc_timestamp=soc_timestamp)


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
        log.debug("Loop: "+str(counter)+", State: "+str(state))
    log.info("Status nach Aufwecken: "+str(state))
    if state != "online":
        raise Exception("EV konnte nicht geweckt werden.")


def create_vehicle(vehicle_config: TeslaSoc, vehicle: int):
    def updater(vehicle_update_data: VehicleUpdateData) -> CarState:
        return fetch(vehicle_config, vehicle_update_data)
    return ConfigurableVehicle(vehicle_config=vehicle_config,
                               component_updater=updater,
                               vehicle=vehicle)


def read_legacy(id: int,
                token_file: str,
                tesla_ev_num: int,
                charge_state: bool):

    log.debug('SoC-Module tesla num: ' + str(id))
    log.debug('SoC-Module tesla token_file: ' + str(token_file))
    log.debug('SoC-Module tesla tesla_ev_num: ' + str(tesla_ev_num))
    log.debug('SoC-Module tesla charge_state: ' + str(charge_state))

    with open(token_file, "r") as f:
        token = json.load(f)
    soc = create_vehicle(TeslaSoc(configuration=TeslaSocConfiguration(
        tesla_ev_num=tesla_ev_num, token=dataclass_from_dict(TeslaSocToken, token))), id)
    soc.update(VehicleUpdateData(charge_state=charge_state))
    with open(token_file, "w") as f:
        f.write(json.dumps(asdict(soc.vehicle_config.configuration.token)))


def main(argv: List[str]):
    run_using_positional_cli_args(read_legacy, argv)


device_descriptor = DeviceDescriptor(configuration_factory=TeslaSoc)
