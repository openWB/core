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
from modules.vehicles.skodaconnect.api import SkodaConnectApi
from modules.vehicles.skodaconnect.config import SkodaConnect, SkodaConnectConfiguration


log = logging.getLogger("soc."+__name__)


class Soc(AbstractSoc):
    def __init__(self, device_config: Union[dict, SkodaConnect], vehicle: int):
        self.config = dataclass_from_dict(SkodaConnect, device_config)
        self.vehicle = vehicle
        self.store = store.get_car_value_store(self.vehicle)
        self.component_info = ComponentInfo(self.vehicle, self.config.name, "vehicle")

    def update(self, charge_state: bool = False) -> None:
        with SingleComponentUpdateContext(self.component_info):
            soc, range = SkodaConnectApi(self.config, self.vehicle).fetch_soc()
            log.info("Result: soc=" + str(soc)+", range=" + str(range))
            if soc > 0 and range > 0.0:
                self.store.set(CarState(soc, range))
            else:
                log.error("Result not stored: soc=" + str(soc)+", range=" + str(range))


def skodaconnect_update(user_id: str, password: str, vin: str, refresh_token: str, charge_point: int):
    log.debug("skodaconnect: userid="+user_id+"vin="+vin+"charge_point="+str(charge_point))
    Soc(
        SkodaConnect(configuration=SkodaConnectConfiguration(user_id, password, vin, refresh_token)),
        charge_point).update()


def main(argv: List[str]):
    run_using_positional_cli_args(skodaconnect_update, argv)


device_descriptor = DeviceDescriptor(configuration_factory=SkodaConnect)
