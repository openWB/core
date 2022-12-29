from typing import Union, List

import logging

from dataclass_utils import dataclass_from_dict
#from helpermodules.cli import run_using_positional_cli_args
from modules.common import store
from modules.common.abstract_device import DeviceDescriptor
from modules.common.abstract_soc import AbstractSoc,SocUpdateData
from modules.common.component_context import SingleComponentUpdateContext
from modules.common.component_state import CarState
from modules.common.fault_state import ComponentInfo
from modules.vehicles.mercedeseq.config import MercedesEQSoc
from modules.vehicles.mercedeseq import api


log = logging.getLogger("soc."+__name__)


class Soc(AbstractSoc):
    def __init__(self, device_config: Union[dict, MercedesEQSoc], vehicle: int):
        self.config = dataclass_from_dict(MercedesEQSoc, device_config)
        self.vehicle = vehicle
        self.store = store.get_car_value_store(self.vehicle)
        self.component_info = ComponentInfo(self.vehicle, self.config.name, "vehicle")

    def update(self, charge_state: bool = False) -> None:
        with SingleComponentUpdateContext(self.component_info):
            soc, range = api.fetch_soc(
                self.config,
                self.vehicle)
            log.info("eq: vehicle="+str(self.vehicle) + ", return: soc=" + str(soc)+", range=" + str(range))
            self.store.set(CarState(soc, range))
            


# def smarteq_update(user_id: str, password: str, vin: str, refreshToken: str, charge_point: int):
# def mercedeseq_update(user_id: str, password: str, vin: str, charge_point: int):
#     log.debug("mercedeseq: userid="+user_id+"vin="+vin+"charge_point="+str(charge_point))
#     Soc(MercedesEQSoc(configuration=MercedesEQSocConfiguration(user_id, password, vin)), charge_point).update(False)


#def main(argv: List[str]):
#     run_using_positional_cli_args(mercedeseq_update, argv)


device_descriptor = DeviceDescriptor(configuration_factory=MercedesEQSoc)