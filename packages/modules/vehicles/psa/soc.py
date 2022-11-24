from typing import Union, List

import logging

from dataclass_utils import dataclass_from_dict
from helpermodules.cli import run_using_positional_cli_args
from modules.common import store
from modules.common.abstract_device import DeviceDescriptor
from modules.common.abstract_soc import AbstractSoc
from modules.common.component_context import SingleComponentUpdateContext
from modules.common.component_state import CarState
from modules.common.fault_state import ComponentInfo
from modules.vehicles.psa import api
from modules.vehicles.psa.config import PSA, PSAConfiguration


log = logging.getLogger("soc."+__name__)


class Soc(AbstractSoc):
    def __init__(self, device_config: Union[dict, PSA], vehicle: int):
        self.config = dataclass_from_dict(PSA, device_config)
        self.vehicle = vehicle
        self.store = store.get_car_value_store(self.vehicle)
        self.component_info = ComponentInfo(self.vehicle, self.config.name, "vehicle")

    def update(self, charge_state: bool = False) -> None:
        with SingleComponentUpdateContext(self.component_info):
            soc, range, soc_timestamp = api.fetch_soc(
                self.config.configuration,
                self.vehicle)
            log.info("psa: vehicle=%s, return: soc=%s, range=%s", self.vehicle, soc, range)
            self.store.set(CarState(soc, range, soc_timestamp))


def psa_update(user_id: str,
               password: str,
               client_id: str,
               client_secret: str,
               manufacturer: str,
               calculate_soc: bool,
               vin: str,
               charge_point: int):
    log.debug("psa-update: user_id=%s, VIN=%s, chargepoint=%s", user_id, vin, charge_point)
    Soc(PSA(configuration=PSAConfiguration(
                                           user_id=user_id,
                                           password=password,
                                           client_id=client_id,
                                           client_secret=client_secret,
                                           manufacturer=manufacturer,
                                           calculate_soc=calculate_soc,
                                           vin=vin)),
        charge_point).update(False)


def main(argv: List[str]):
    run_using_positional_cli_args(psa_update, argv)


device_descriptor = DeviceDescriptor(configuration_factory=PSA)
