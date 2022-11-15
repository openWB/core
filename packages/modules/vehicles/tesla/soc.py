#!/usr/bin/env python3
import json
import logging
import time
from typing import Dict, List, Union

from dataclass_utils import asdict, dataclass_from_dict
from helpermodules.cli import run_using_positional_cli_args
from modules.common import store
from modules.common.abstract_device import DeviceDescriptor
from modules.common.abstract_soc import AbstractSoc
from modules.common.component_context import SingleComponentUpdateContext
from modules.common.component_state import CarState
from modules.common.fault_state import ComponentInfo, FaultState
from modules.vehicles.tesla import api
from modules.vehicles.tesla.config import TeslaSoc, TeslaSocConfiguration, TeslaSocToken

log = logging.getLogger("soc."+__name__)


class Soc(AbstractSoc):
    def __init__(self, soc_config: Union[Dict, TeslaSoc], vehicle: int):
        self.soc_config = dataclass_from_dict(TeslaSoc, soc_config)
        self.vehicle = vehicle
        self.store = store.get_car_value_store(self.vehicle)
        self.component_info = ComponentInfo(self.vehicle, self.soc_config.name, "vehicle")

    def update(self, charge_state: bool = False) -> None:
        with SingleComponentUpdateContext(self.component_info):
            self.soc_config.configuration.token = api.validate_token(self.soc_config.configuration.token)
            if charge_state is False:
                self.__wake_up_car()
            soc, range = api.request_soc_range(
                vehicle=self.soc_config.configuration.tesla_ev_num, token=self.soc_config.configuration.token)
            self.store.set(CarState(soc, range))

    def __wake_up_car(self):
        log.debug("Tesla"+str(self.vehicle)+": Waking up car.")
        counter = 0
        state = "offline"
        while counter <= 12:
            state = api.post_wake_up_command(
                vehicle=self.soc_config.configuration.tesla_ev_num, token=self.soc_config.configuration.token)
            if state == "online":
                break
            counter = counter+1
            time.sleep(5)
            log.debug("Tesla "+str(self.vehicle)+": Loop: "+str(counter)+", State: "+str(state))
        log.info("Tesla "+str(self.vehicle)+": Status nach Aufwecken: "+str(state))
        if state != "online":
            raise FaultState.error("EV"+str(self.vehicle)+" konnte nicht geweckt werden.")


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
    soc = Soc(TeslaSoc(configuration=TeslaSocConfiguration(
        tesla_ev_num=tesla_ev_num, token=dataclass_from_dict(TeslaSocToken, token))), id)
    soc.update(charge_state)
    with open(token_file, "w") as f:
        f.write(json.dumps(asdict(soc.soc_config.configuration.token)))


def main(argv: List[str]):
    run_using_positional_cli_args(read_legacy, argv)


device_descriptor = DeviceDescriptor(configuration_factory=TeslaSoc)
