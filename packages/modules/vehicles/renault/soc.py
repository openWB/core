from typing import Union, List

import logging

from dataclass_utils import dataclass_from_dict
from helpermodules.cli import run_using_positional_cli_args
from modules.common import store
from modules.common.abstract_device import DeviceDescriptor
from modules.common.abstract_soc import AbstractSoc, SocUpdateData
from modules.common.component_context import SingleComponentUpdateContext
from modules.common.fault_state import ComponentInfo
from modules.vehicles.renault import api
from modules.vehicles.renault.config import Renault, RenaultConfiguration


log = logging.getLogger("soc."+__name__)


class Soc(AbstractSoc):
    def __init__(self, device_config: Union[dict, Renault], vehicle: int):
        self.config = dataclass_from_dict(Renault, device_config)
        self.vehicle = vehicle
        self.store = store.get_car_value_store(self.vehicle)
        self.component_info = ComponentInfo(self.vehicle, self.config.name, "vehicle")

    def update(self, soc_update_data: SocUpdateData) -> None:
        with SingleComponentUpdateContext(self.component_info):
            self.store.set(api.fetch_soc(self.config.configuration))


def renault_update(user_id: str, password: str, location: str, country: str, vin: str, charge_point: int):
    log.debug("renault: user_id=" + user_id + "vin=" + vin + "charge_point=" + str(charge_point))
    Soc(Renault(configuration=RenaultConfiguration(charge_point, user_id, password, location, country, vin)),
        charge_point).update(SocUpdateData())


def main(argv: List[str]):
    run_using_positional_cli_args(renault_update, argv)


device_descriptor = DeviceDescriptor(configuration_factory=Renault)
