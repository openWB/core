from typing import Union
import logging
from dataclass_utils import dataclass_from_dict
from modules.common import store
from modules.common.abstract_device import DeviceDescriptor
from modules.common.abstract_soc import AbstractSoc
from modules.common.component_context import SingleComponentUpdateContext
from modules.common.component_state import CarState
from modules.common.fault_state import ComponentInfo
from modules.vehicles.mercedeseq.config import MercedesEQSoc
import modules.vehicles.mercedeseq.api as api


log = logging.getLogger("soc."+__name__)


class Soc(AbstractSoc):
    def __init__(self, device_config: Union[dict, MercedesEQSoc], vehicle: int):
        self.config = dataclass_from_dict(MercedesEQSoc, device_config)
        self.vehicle = vehicle
        self.store = store.get_car_value_store(self.vehicle)
        self.component_info = ComponentInfo(self.vehicle, self.config.name, "vehicle")

    def update(self, charge_state: bool = False) -> None:
        # # if self.config.configuration.code == None and self.config.configuration.token.access_token == None:
        # if  self.config.configuration.token.access_token == None:
        #     # error: "Bitte Link in der Konfiguration anklicken" triggert Aufruf der Callback-URL
        #     pass
        # # elif self.config.configuration.code != None and self.config.configuration.token.access_token == None:
        #     # auth.py um Token abzuholen

        # else:
        with SingleComponentUpdateContext(self.component_info):
            soc, range = api.fetch_soc(self.config, self.vehicle)
            # log.info("eq: vehicle="+str(self.vehicle) + ", return: soc=" + str(soc)+", range=" + str(range))
            self.store.set(CarState(soc, range))


device_descriptor = DeviceDescriptor(configuration_factory=MercedesEQSoc)
