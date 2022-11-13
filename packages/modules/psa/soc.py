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
from modules.psa import api
from modules.psa.config import PSA, PSAConfiguration


log = logging.getLogger("soc."+__name__)


class Soc(AbstractSoc):
    def __init__(self, device_config: Union[dict, PSA], vehicle: int):
        self.config = dataclass_from_dict(PSA, device_config)
        self.vehicle = vehicle
        self.store = store.get_car_value_store(self.vehicle)
        self.component_info = ComponentInfo(self.vehicle, self.config.name, "vehicle")

    def update(self, charge_state: bool = False) -> None:
        with SingleComponentUpdateContext(self.component_info):
            soc, range = api.fetch_soc(
                self.config.configuration.userid,
                self.config.configuration.password,
                self.config.configuration.client_id,
                self.config.configuration.client_secret,
                self.config.configuration.manufacturer,
                self.config.configuration.soccalc,
                self.config.configuration.vin,
                self.vehicle)
            log.info("psa: vehicle="+str(self.vehicle) + ", return: soc=" + str(soc)+", range=" + str(range))
            self.store.set(CarState(soc, range))


def psa_update(userid: str,
               password: str,
               client_id: str,
               client_secret: str,
               manufacturer: str,
               soccalc: str, vin: str,
               charge_point: int):
    log.debug("psa-psa-update: userid="+userid+"vin="+vin+"charge_point="+str(charge_point))
    Soc(PSA(configuration=PSAConfiguration(charge_point,
                                           userid,
                                           password,
                                           client_id,
                                           client_secret,
                                           manufacturer,
                                           soccalc,
                                           vin)),
        charge_point).update(False)


def main(argv: List[str]):
    run_using_positional_cli_args(psa_update, argv)


device_descriptor = DeviceDescriptor(configuration_factory=PSA)
