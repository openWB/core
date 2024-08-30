#!/usr/bin/env python3
from typing import List

import logging
import time

from helpermodules.cli import run_using_positional_cli_args
from modules.common import store
from modules.common.abstract_device import DeviceDescriptor
from modules.common.abstract_vehicle import VehicleUpdateData
from modules.common.component_state import CarState
from modules.common.configurable_vehicle import ConfigurableVehicle
from modules.vehicles.leaf.config import LeafSoc, LeafConfiguration

import pycarwings2

log = logging.getLogger(__name__)


def fetch_soc(username, password, chargepoint) -> CarState:

    region = "NE"

    def getNissanSession():     # open Https session with Nissan server
        log.debug("LP%s: login = %s, region = %s" % (chargepoint, username, region))
        s = pycarwings2.Session(username, password, region)
        leaf = s.get_leaf()
        time.sleep(1)           # give Nissan server some time
        return leaf

    def readSoc(leaf):          # get SoC from Nissan server
        leaf_info = leaf.get_latest_battery_status()
        bat_percent = int(leaf_info.battery_percent)
        log.debug("LP%s: Battery status %s" % (chargepoint, bat_percent))
        return bat_percent

    def requestSoc(leaf):       # request Nissan server to request last SoC from car
        log.debug("LP%s: Request SoC Update" % (chargepoint))
        key = leaf.request_update()
        status = leaf.get_status_from_update(key)
        sleepsecs = 20
        for i in range(0, 9):
            log.debug("Waiting {0} seconds".format(sleepsecs))
            time.sleep(sleepsecs)
            status = leaf.get_status_from_update(key)
            if status is not None:
                break
        log.debug("LP%s: Finished updating" % (chargepoint))

    leaf = getNissanSession()   # start Https session with Nissan Server
    readSoc(leaf)               # old SoC needs to be read from server before requesting new SoC from car
    time.sleep(1)               # give Nissan server some time
    requestSoc(leaf)            # Nissan server to request new SoC from car
    time.sleep(1)               # give Nissan server some time
    soc = readSoc(leaf)         # final read of SoC from server
    return CarState(soc)


def create_vehicle(vehicle_config: LeafSoc, vehicle: int):
    def updater(vehicle_update_data: VehicleUpdateData) -> CarState:
        return fetch_soc(
            vehicle_config.configuration.user_id,
            vehicle_config.configuration.password,
            vehicle)
    return ConfigurableVehicle(vehicle_config=vehicle_config, component_updater=updater, vehicle=vehicle)


def leaf_update(user_id: str, password: str, charge_point: int):
    log.debug("Leaf: user_id="+user_id+"charge_point="+str(charge_point))
    vehicle_config = LeafSoc(configuration=LeafConfiguration(charge_point, user_id, password))
    store.get_car_value_store(charge_point).store.set(fetch_soc(
        vehicle_config.configuration.user_id,
        vehicle_config.configuration.password,
        charge_point))


def main(argv: List[str]):
    run_using_positional_cli_args(leaf_update, argv)


device_descriptor = DeviceDescriptor(configuration_factory=LeafSoc)
